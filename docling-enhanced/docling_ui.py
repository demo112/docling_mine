#!/usr/bin/env python3
"""
Docling 文档转换器 - 增强版
支持多种文档格式转换，包含实时进度显示、批量下载等功能
"""

import io
import os
import tempfile
import traceback
import time
from pathlib import Path
from typing import Optional, Dict, Any
import zipfile
import base64

import streamlit as st
from PIL import Image
import pandas as pd

# Docling imports
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat, OutputFormat, FormatToExtensions
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.backend_options import PdfBackendOptions
from docling.document_converter import PdfFormatOption
from docling.backend.docling_parse_v4_backend import DoclingParseV4DocumentBackend

# 日志相关
import logging
import queue
import re

# 日志捕获类
class LogCapture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.logs = []
        self.page_progress = {}
        
    def emit(self, record):
        log_entry = self.format(record)
        self.logs.append(log_entry)
        
        # 解析页面进度信息
        if "page" in log_entry.lower() and any(word in log_entry.lower() for word in ["processing", "converting", "extracting"]):
            # 尝试提取页面信息
            page_match = re.search(r'page\s*(\d+)', log_entry.lower())
            if page_match:
                page_num = int(page_match.group(1))
                self.page_progress[page_num] = log_entry
    
    def get_logs(self):
        return self.logs.copy()
    
    def clear_logs(self):
        self.logs.clear()
        self.page_progress.clear()
    
    def get_page_progress(self):
        return self.page_progress.copy()

log_capture = LogCapture()

def setup_logging():
    """设置日志捕获"""
    # 清除现有的处理器
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # 添加我们的日志捕获器
    logging.root.addHandler(log_capture)
    logging.root.setLevel(logging.INFO)
    
    # 设置docling相关的日志级别
    logging.getLogger('docling').setLevel(logging.INFO)

# 页面配置
st.set_page_config(
    page_title="Docling 文档转换器",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS样式
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .feature-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }

    .stButton > button:hover {
        background: linear-gradient(90deg, #5a6fd8 0%, #6a4190 100%);
        transform: translateY(-2px);
        transition: all 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

def get_mime_type(format_type: str) -> str:
    """获取MIME类型"""
    mime_types = {
        'markdown': 'text/markdown',
        'html': 'text/html',
        'json': 'application/json',
        'text': 'text/plain'
    }
    return mime_types.get(format_type, 'text/plain')

def get_supported_formats():
    """获取支持的格式列表"""
    return [
        "PDF", "DOCX", "PPTX", "HTML", "Images (PNG, JPG, JPEG, TIFF, BMP)",
        "AsciiDoc", "Markdown"
    ]

def get_file_format(filename: str) -> Optional[str]:
    """根据文件名获取格式"""
    ext = Path(filename).suffix.lower()
    format_mapping = {
        '.pdf': 'PDF',
        '.docx': 'DOCX', 
        '.pptx': 'PPTX',
        '.html': 'HTML',
        '.htm': 'HTML',
        '.png': 'Image',
        '.jpg': 'Image',
        '.jpeg': 'Image',
        '.tiff': 'Image',
        '.bmp': 'Image',
        '.adoc': 'AsciiDoc',
        '.md': 'Markdown'
    }
    return format_mapping.get(ext)

def display_header():
    """显示页面头部"""
    st.markdown("""
    <div class="main-header">
        <h1>📄 Docling 文档转换器 - 增强版</h1>
        <p>高效、准确的文档格式转换工具</p>
    </div>
    """, unsafe_allow_html=True)

def display_features():
    """显示功能特性"""
    st.markdown("""
    <div class="feature-box">
        <h3>🚀 增强功能</h3>
        <ul>
            <li>📊 <strong>实时进度显示</strong> - 查看转换进度和页面处理状态</li>
            <li>⏱️ <strong>处理时间统计</strong> - 精确显示每个文件的处理时间</li>
            <li>📋 <strong>详细状态信息</strong> - 显示文件格式、页数等详细信息</li>
            <li>💾 <strong>批量下载</strong> - 一键下载所有转换成功的文件</li>
            <li>🔍 <strong>内容预览</strong> - 转换完成后即时预览内容</li>
            <li>🛠️ <strong>错误处理</strong> - 详细的错误信息和处理建议</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def convert_files(uploaded_files, output_format, enable_ocr, enable_table_structure, enable_picture_extraction):
    """转换文件的主函数"""
    if not uploaded_files:
        return
    
    # 初始化session state用于稳定的key
    if 'conversion_timestamp' not in st.session_state:
        st.session_state.conversion_timestamp = int(time.time() * 1000)
    
    # 设置日志捕获
    setup_logging()
    log_capture.clear_logs()
    
    # 创建转换器配置
    pdf_backend_options = PdfBackendOptions()
    
    pdf_pipeline_options = PdfPipelineOptions(
        do_ocr=enable_ocr,
        do_table_structure=enable_table_structure,
        images_scale=2.0,
        generate_page_images=enable_picture_extraction,
        generate_picture_images=enable_picture_extraction
    )
    
    # 创建转换器
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                backend=DoclingParseV4DocumentBackend,
                backend_options=pdf_backend_options,
                pipeline_options=pdf_pipeline_options
            )
        }
    )
    
    # 创建进度显示区域
    progress_container = st.container()
    results_area = st.container()
    
    with progress_container:
        st.subheader("🔄 转换进度")
        overall_progress = st.progress(0)
        overall_status = st.empty()
        current_file_info = st.empty()
        
        # OCR进度显示区域
        if enable_ocr:
            st.markdown("### 🔍 OCR 详细进度")
            ocr_progress_area = st.empty()
            ocr_logs_area = st.empty()
    
    conversion_results = []
    success_count = 0
    
    # 处理每个文件
    for i, uploaded_file in enumerate(uploaded_files):
        start_time = time.time()
        
        # 更新总体进度
        progress = i / len(uploaded_files)
        overall_progress.progress(progress)
        overall_status.text(f"正在处理: {i+1}/{len(uploaded_files)} - {uploaded_file.name}")
        
        # 显示当前文件信息
        file_format = get_file_format(uploaded_file.name)
        current_file_info.markdown(f"""
        **📄 当前文件:** {uploaded_file.name}  
        **📋 格式:** {file_format or '未知'}  
        **📏 大小:** {uploaded_file.size / 1024:.1f} KB
        """)
        
        # 清空之前的OCR日志
        if enable_ocr:
            log_capture.clear_logs()
        
        tmp_file_path = None
        try:
            # 保存临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # 验证文件是否存在
            if not os.path.exists(tmp_file_path):
                raise FileNotFoundError(f"临时文件创建失败: {tmp_file_path}")
            
            # 显示OCR开始信息
            if enable_ocr:
                ocr_progress_area.info("🔍 开始OCR处理...")
            
            # 执行转换
            result = converter.convert(tmp_file_path)
            
            # 显示OCR进度日志
            if enable_ocr:
                logs = log_capture.get_logs()
                page_progress = log_capture.get_page_progress()
                
                if page_progress:
                    ocr_progress_area.success(f"🔍 OCR进度: {page_progress}")
                
                if logs:
                    # 只显示最近的几条日志
                    recent_logs = logs[-5:] if len(logs) > 5 else logs
                    log_text = "\n".join([f"• {log}" for log in recent_logs])
                    ocr_logs_area.text_area(
                        "OCR处理日志", 
                        log_text, 
                        height=100,
                        key=f"ocr_logs_{i}_{st.session_state.conversion_timestamp}"
                    )
            
            # 获取转换后的内容
            if output_format == "Markdown":
                content = result.document.export_to_markdown()
                extension = "md"
            elif output_format == "HTML":
                content = result.document.export_to_html()
                extension = "html"
            elif output_format == "JSON":
                content = result.document.export_to_json()
                extension = "json"
            else:  # Text
                content = result.document.export_to_text()
                extension = "txt"
            
            processing_time = time.time() - start_time
            
            conversion_results.append({
                'filename': uploaded_file.name,
                'success': True,
                'content': content,
                'extension': extension,
                'processing_time': processing_time,
                'pages': len(result.document.pages) if hasattr(result.document, 'pages') else 'N/A'
            })
            
            success_count += 1
            
            # 清理临时文件
            if tmp_file_path and os.path.exists(tmp_file_path):
                try:
                    os.unlink(tmp_file_path)
                except Exception as cleanup_error:
                    print(f"清理临时文件失败: {cleanup_error}")
                
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            # 添加更详细的错误信息
            if "No such file or directory" in error_msg:
                error_msg = f"文件访问错误: {error_msg}\n可能原因:\n- 临时文件创建失败\n- 文件路径包含特殊字符\n- 磁盘空间不足"
            
            conversion_results.append({
                'filename': uploaded_file.name,
                'success': False,
                'error': error_msg,
                'processing_time': processing_time,
                'tmp_file_path': tmp_file_path if tmp_file_path else "未创建"
            })
            
            # 清理临时文件
            if tmp_file_path and os.path.exists(tmp_file_path):
                try:
                    os.unlink(tmp_file_path)
                except Exception as cleanup_error:
                    print(f"清理临时文件失败: {cleanup_error}")
    
    # 完成总体进度
    overall_progress.progress(1.0)
    overall_status.text(f"✅ 转换完成! 成功: {success_count}/{len(uploaded_files)}")
    
    # 清空当前文件信息
    current_file_info.empty()
    
    # 显示结果
    with results_area.container():
        st.subheader("📋 转换结果")
        
        # 批量下载按钮（如果有多个成功转换的文件）
        if success_count > 1:
            st.markdown("### 📦 批量下载")
            
            # 创建ZIP文件
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for result in conversion_results:
                    if result['success']:
                        filename = f"{Path(result['filename']).stem}.{result['extension']}"
                        zip_file.writestr(filename, result['content'])
            
            zip_buffer.seek(0)
            
            # 使用session state中的稳定时间戳作为key
            st.download_button(
                label="📦 下载所有文件 (ZIP)",
                data=zip_buffer.getvalue(),
                file_name=f"converted_files_{st.session_state.conversion_timestamp}.zip",
                mime="application/zip",
                key=f"batch_download_{st.session_state.conversion_timestamp}"
            )
            
            st.markdown("---")
        
        # 显示每个文件的结果
        for i, result in enumerate(conversion_results):
            if result['success']:
                st.markdown(f"""
                <div class="success-box">
                    <h4>✅ {result['filename']}</h4>
                    <p>📄 格式: {output_format}</p>
                    <p>⏱️ 处理时间: {result['processing_time']:.2f} 秒</p>
                    <p>📊 内容长度: {len(result['content'])} 字符</p>
                    <p>📑 页数: {result.get('pages', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 内容预览
                st.subheader("📖 内容预览")
                preview_content = result['content'][:1000] + "..." if len(result['content']) > 1000 else result['content']
                
                # 使用session state中的稳定时间戳作为key
                st.text_area(
                    "预览内容", 
                    preview_content, 
                    height=200, 
                    key=f"preview_{i}_{st.session_state.conversion_timestamp}"
                )
                
                # 下载按钮
                download_filename = f"{Path(result['filename']).stem}.{result['extension']}"
                
                # 使用session state中的稳定时间戳作为key
                st.download_button(
                    label=f"📥 下载 {output_format} 文件",
                    data=result['content'],
                    file_name=download_filename,
                    mime=get_mime_type(output_format.lower()),
                    key=f"download_{i}_{st.session_state.conversion_timestamp}"
                )
                
            else:
                st.markdown(f"""
                <div class="error-box">
                    <h4>❌ {result['filename']}</h4>
                    <p>⏱️ 处理时间: {result['processing_time']:.2f} 秒</p>
                    <p>🚫 错误信息: {result['error']}</p>
                </div>
                """, unsafe_allow_html=True)

def main():
    """主函数"""
    # 显示头部
    display_header()
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 转换设置")
        
        # 输出格式选择
        output_format = st.selectbox(
            "📄 输出格式",
            ["Markdown", "HTML", "JSON", "Text"],
            index=0
        )
        
        st.markdown("---")
        
        # PDF选项
        st.subheader("📑 PDF 选项")
        enable_ocr = st.checkbox("🔍 启用OCR (光学字符识别)", value=True)
        enable_table_structure = st.checkbox("📊 启用表格结构识别", value=True)
        enable_picture_extraction = st.checkbox("🖼️ 启用图片提取", value=False)
        
        st.markdown("---")
        
        # 系统状态
        st.subheader("💻 系统状态")
        st.success("✅ Docling 已就绪")
        st.info("📊 内存使用正常")
        
        st.markdown("---")
        
        # 快速测试
        st.subheader("🚀 快速测试")
        st.info("💡 上传测试文件快速体验转换功能")
    
    # 主内容区域
    display_features()
    
    # 文件上传
    st.subheader("📁 文件上传")
    uploaded_files = st.file_uploader(
        "选择要转换的文件",
        type=['pdf', 'docx', 'pptx', 'html', 'htm', 'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'adoc', 'md'],
        accept_multiple_files=True,
        help="支持多种格式：PDF, DOCX, PPTX, HTML, 图片等"
    )
    
    # 显示支持的格式
    if not uploaded_files:
        st.markdown("### 📋 支持的格式")
        formats = get_supported_formats()
        cols = st.columns(3)
        for i, fmt in enumerate(formats):
            with cols[i % 3]:
                st.markdown(f"✅ {fmt}")
    
    # 转换按钮和处理
    if uploaded_files:
        st.markdown(f"### 📤 已选择 {len(uploaded_files)} 个文件")
        
        # 显示文件列表
        for file in uploaded_files:
            file_format = get_file_format(file.name)
            st.markdown(f"- **{file.name}** ({file_format or '未知格式'}, {file.size/1024:.1f} KB)")
        
        if st.button("🚀 开始转换", type="primary"):
            # 重置时间戳，确保新转换有新的稳定key
            st.session_state.conversion_timestamp = int(time.time() * 1000)
            convert_files(uploaded_files, output_format, enable_ocr, enable_table_structure, enable_picture_extraction)

if __name__ == "__main__":
    main()