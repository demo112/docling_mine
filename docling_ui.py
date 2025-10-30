#!/usr/bin/env python3
"""
Docling 可视化界面
基于 Streamlit 的 Web 应用，提供文档转换的图形化界面
"""

import io
import os
import tempfile
import traceback
from pathlib import Path
from typing import Optional, Dict, Any
import zipfile
import base64

import streamlit as st
from PIL import Image
import pandas as pd

# Docling 核心导入
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat, OutputFormat, FormatToExtensions
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.backend_options import PdfBackendOptions
from docling.document_converter import PdfFormatOption

# 日志和进度相关导入
import logging
import queue
import re

# 日志捕获类
class LogCapture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_queue = queue.Queue()
        self.page_progress = {"current": 0, "total": 0}
        
    def emit(self, record):
        log_entry = self.format(record)
        self.log_queue.put(log_entry)
        
        # 解析页面进度信息
        if "Finished converting pages" in log_entry:
            # 匹配格式: "Finished converting pages 5/10 time=1.234"
            match = re.search(r"Finished converting pages (\d+)/(\d+)", log_entry)
            if match:
                current = int(match.group(1))
                total = int(match.group(2))
                self.page_progress = {"current": current, "total": total}
    
    def get_logs(self):
        logs = []
        while not self.log_queue.empty():
            try:
                logs.append(self.log_queue.get_nowait())
            except queue.Empty:
                break
        return logs
    
    def get_page_progress(self):
        return self.page_progress.copy()

# 全局日志捕获器
log_capture = LogCapture()

def setup_logging():
    """设置日志捕获"""
    # 获取 docling 的日志记录器
    docling_logger = logging.getLogger('docling')
    docling_logger.setLevel(logging.DEBUG)
    
    # 添加我们的日志捕获器
    if log_capture not in docling_logger.handlers:
        docling_logger.addHandler(log_capture)


# 页面配置
st.set_page_config(
    page_title="Docling 文档转换器",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
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


def get_supported_formats() -> Dict[str, list]:
    """获取支持的文件格式"""
    return {
        "文档格式": {
            "PDF": ["pdf"],
            "Word": ["docx", "dotx", "docm", "dotm"],
            "PowerPoint": ["pptx", "potx", "ppsx", "pptm", "potm", "ppsm"],
            "Excel": ["xlsx", "xlsm"],
            "HTML": ["html", "htm", "xhtml"],
            "Markdown": ["md"],
            "CSV": ["csv"],
        },
        "图像格式": {
            "常见图像": ["jpg", "jpeg", "png", "tif", "tiff", "bmp", "webp"]
        },
        "音频格式": {
            "音频文件": ["wav", "mp3", "m4a", "aac", "ogg", "flac"],
            "视频文件": ["mp4", "avi", "mov"]
        },
        "其他格式": {
            "AsciiDoc": ["adoc", "asciidoc", "asc"],
            "XML": ["xml", "nxml"],
            "VTT": ["vtt"],
            "JSON": ["json"]
        }
    }


def display_header():
    """显示页面头部"""
    st.markdown("""
    <div class="main-header">
        <h1>📄 Docling 文档转换器</h1>
        <p>强大的多格式文档处理工具 - 支持 PDF、Word、Excel、图像等多种格式</p>
    </div>
    """, unsafe_allow_html=True)


def display_features():
    """显示功能特性"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-box">
            <h4>🔄 多格式支持</h4>
            <p>支持 PDF、DOCX、PPTX、XLSX、HTML、图像、音频等多种格式</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-box">
            <h4>🧠 智能解析</h4>
            <p>高级 PDF 理解、表格结构识别、OCR 文字识别</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-box">
            <h4>📤 多种输出</h4>
            <p>支持 Markdown、HTML、JSON、纯文本等多种输出格式</p>
        </div>
        """, unsafe_allow_html=True)


def get_file_format(filename: str) -> Optional[InputFormat]:
    """根据文件名获取输入格式"""
    if not filename:
        return None
    
    extension = filename.lower().split('.')[-1]
    
    for format_type, extensions in FormatToExtensions.items():
        if extension in extensions:
            return format_type
    
    return None


def create_download_link(content: str, filename: str, link_text: str) -> str:
    """创建下载链接"""
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:text/plain;base64,{b64}" download="{filename}">{link_text}</a>'
    return href


def main():
    """主函数"""
    display_header()
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 转换设置")
        
        # 输出格式选择
        output_format = st.selectbox(
            "选择输出格式",
            options=[
                ("Markdown", "markdown"),
                ("HTML", "html"),
                ("JSON", "json"),
                ("纯文本", "text")
            ],
            format_func=lambda x: x[0],
            help="选择文档转换后的输出格式"
        )
        
        # PDF 特殊选项
        st.subheader("📄 PDF 处理选项")
        enable_ocr = st.checkbox("启用 OCR 文字识别", value=True, help="对扫描的PDF进行文字识别")
        enable_table_structure = st.checkbox("启用表格结构识别", value=True, help="识别和提取表格结构")
        
        # 高级选项
        with st.expander("🔧 高级选项"):
            max_pages = st.number_input("最大页数限制", min_value=1, max_value=1000, value=100)
            page_range_start = st.number_input("起始页码", min_value=1, value=1)
            page_range_end = st.number_input("结束页码", min_value=1, value=100)
        
        # 系统状态
        st.subheader("📊 系统状态")
        st.write("🟢 界面运行正常")
        st.write("🟢 Docling 核心已加载")
        
        # 快速测试
        with st.expander("🧪 快速测试"):
            st.write("如果上传文件后没有反应，可能的原因：")
            st.write("• PDF 文件较大，OCR 处理需要时间")
            st.write("• 文件格式不支持")
            st.write("• 网络连接问题")
            
            if st.button("🔄 刷新页面", help="如果界面卡住可以尝试刷新"):
                st.rerun()
    
    # 主内容区域
    display_features()
    
    # 文件上传区域
    st.header("📁 文件上传")
    
    # 显示支持的格式
    with st.expander("📋 查看支持的文件格式"):
        formats = get_supported_formats()
        for category, format_dict in formats.items():
            st.subheader(category)
            for format_name, extensions in format_dict.items():
                st.write(f"**{format_name}**: {', '.join(extensions)}")
    
    # 文件上传组件
    uploaded_files = st.file_uploader(
        "选择要转换的文件",
        accept_multiple_files=True,
        help="支持多文件同时上传，支持的格式包括 PDF、Word、Excel、图像等"
    )
    
    if uploaded_files:
        st.success(f"已上传 {len(uploaded_files)} 个文件")
        
        # 显示上传的文件信息
        file_info = []
        for file in uploaded_files:
            file_format = get_file_format(file.name)
            file_info.append({
                "文件名": file.name,
                "大小": f"{file.size / 1024:.1f} KB",
                "格式": file_format.value if file_format else "未知",
                "状态": "✅ 已识别" if file_format else "❌ 不支持"
            })
        
        df = pd.DataFrame(file_info)
        st.dataframe(df, width='stretch')
        
        # 转换按钮
        if st.button("🚀 开始转换", type="primary"):
            convert_documents(uploaded_files, output_format[1], {
                'enable_ocr': enable_ocr,
                'enable_table_structure': enable_table_structure,
                'max_pages': max_pages,
                'page_range': (page_range_start, page_range_end)
            })


def convert_documents(uploaded_files, output_format: str, options: Dict[str, Any]):
    """转换文档"""
    st.header("🔄 转换进度")
    
    # 设置日志捕获
    setup_logging()
    
    # 创建进度条和状态显示
    progress_bar = st.progress(0)
    status_text = st.empty()
    time_text = st.empty()
    
    # 页面进度显示（仅对 PDF 显示）
    page_progress_container = st.empty()
    page_progress_bar = st.empty()
    page_status_text = st.empty()
    
    # 结果容器
    results_container = st.container()
    
    try:
        # 配置转换器
        status_text.text("🔧 正在初始化转换器...")
        
        pdf_options = PdfPipelineOptions(
            do_ocr=options['enable_ocr'],
            do_table_structure=options['enable_table_structure']
        )
        
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options)
            }
        )
        
        total_files = len(uploaded_files)
        results = []
        
        import time
        start_time = time.time()
        
        for i, uploaded_file in enumerate(uploaded_files):
            file_start_time = time.time()
            
            # 更新状态显示
            status_text.text(f"📄 正在处理文件 {i+1}/{total_files}: {uploaded_file.name}")
            progress_bar.progress(i / total_files)
            
            # 重置页面进度
            log_capture.page_progress = {"current": 0, "total": 0}
            
            try:
                # 获取文件格式
                file_format = get_file_format(uploaded_file.name)
                if not file_format:
                    results.append({
                        'filename': uploaded_file.name,
                        'status': 'error',
                        'message': '不支持的文件格式'
                    })
                    continue
                
                # 显示文件处理步骤
                with st.expander(f"📋 处理详情: {uploaded_file.name}", expanded=False):
                    step_container = st.container()
                    with step_container:
                        st.write("🔄 创建临时文件...")
                
                # 创建临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                with step_container:
                    st.write("⚙️ 开始文档转换...")
                    if options['enable_ocr']:
                        st.write("👁️ OCR 文字识别已启用，处理可能需要较长时间...")
                
                # 如果是 PDF，显示页面进度
                if file_format == InputFormat.PDF:
                    page_progress_container.info("📄 PDF 页面处理进度:")
                    page_progress_bar.progress(0.0)
                    page_status_text.text("准备处理页面...")
                    
                    # 启动页面进度监控
                    import threading
                    import time as time_module
                    
                    def update_page_progress():
                        """更新页面进度显示"""
                        last_progress = {"current": 0, "total": 0}
                        while True:
                            current_progress = log_capture.get_page_progress()
                            if current_progress != last_progress and current_progress["total"] > 0:
                                progress_ratio = current_progress["current"] / current_progress["total"]
                                page_progress_bar.progress(progress_ratio)
                                page_status_text.text(f"📄 处理页面: {current_progress['current']}/{current_progress['total']}")
                                last_progress = current_progress.copy()
                            time_module.sleep(0.1)
                    
                    # 启动监控线程
                    monitor_thread = threading.Thread(target=update_page_progress, daemon=True)
                    monitor_thread.start()
                
                # 执行转换
                result = converter.convert(tmp_file_path)
                
                with step_container:
                    st.write("📝 生成输出内容...")
                
                # 根据输出格式生成内容
                if output_format == "markdown":
                    content = result.document.export_to_markdown()
                elif output_format == "html":
                    content = result.document.export_to_html()
                elif output_format == "json":
                    content = result.document.export_to_json()
                elif output_format == "text":
                    content = result.document.export_to_text()
                else:
                    content = result.document.export_to_markdown()
                
                file_end_time = time.time()
                processing_time = file_end_time - file_start_time
                
                results.append({
                    'filename': uploaded_file.name,
                    'status': 'success',
                    'content': content,
                    'format': output_format,
                    'pages': len(result.document.pages) if hasattr(result.document, 'pages') else 1,
                    'processing_time': processing_time
                })
                
                with step_container:
                    st.write(f"✅ 转换完成！耗时: {processing_time:.1f} 秒")
                
                # 显示最终页面进度
                if file_format == InputFormat.PDF:
                    final_progress = log_capture.get_page_progress()
                    if final_progress["total"] > 0:
                        page_progress_bar.progress(1.0)
                        page_status_text.text(f"✅ 完成: {final_progress['total']}/{final_progress['total']} 页")
                    else:
                        page_status_text.text("✅ PDF 处理完成")
                
                # 清理临时文件
                os.unlink(tmp_file_path)
                
            except Exception as e:
                file_end_time = time.time()
                processing_time = file_end_time - file_start_time
                
                error_msg = str(e)
                results.append({
                    'filename': uploaded_file.name,
                    'status': 'error',
                    'message': error_msg,
                    'processing_time': processing_time
                })
                
                with step_container:
                    st.write(f"❌ 转换失败！耗时: {processing_time:.1f} 秒")
                    st.error(f"错误: {error_msg}")
        
        # 更新最终进度
        progress_bar.progress(1.0)
        
        total_time = time.time() - start_time
        status_text.text("✅ 所有文件处理完成!")
        time_text.text(f"⏱️ 总耗时: {total_time:.1f} 秒")
        
        # 清除页面进度显示
        page_progress_container.empty()
        page_progress_bar.empty()
        page_status_text.empty()
        
        # 显示结果
        display_results(results, results_container)
        
    except Exception as e:
        st.error(f"转换过程中发生错误: {str(e)}")
        st.error("详细错误信息:")
        st.code(traceback.format_exc())
        
        # 显示调试信息
        st.info("💡 提示：如果是 PDF 文件转换失败，可以尝试：")
        st.write("- 关闭 OCR 选项")
        st.write("- 减少页数限制")
        st.write("- 检查 PDF 文件是否损坏")


def display_results(results, container):
    """显示转换结果"""
    with container:
        st.header("📊 转换结果")
        
        # 统计信息
        success_count = sum(1 for r in results if r['status'] == 'success')
        error_count = len(results) - success_count
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总文件数", len(results))
        with col2:
            st.metric("成功转换", success_count)
        with col3:
            st.metric("转换失败", error_count)
        
        # 详细结果
        for i, result in enumerate(results):
            with st.expander(f"📄 {result['filename']}", expanded=True):
                if result['status'] == 'success':
                    processing_time = result.get('processing_time', 0)
                    st.markdown(f"""
                    <div class="success-box">
                        <strong>✅ 转换成功</strong><br>
                        格式: {result['format']}<br>
                        页数: {result.get('pages', 'N/A')}<br>
                        耗时: {processing_time:.1f} 秒
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 内容预览
                    st.subheader("📖 内容预览")
                    preview_content = result['content'][:1000] + "..." if len(result['content']) > 1000 else result['content']
                    
                    if result['format'] == 'html':
                        st.components.v1.html(preview_content, height=300, scrolling=True)
                    else:
                        st.text_area("预览内容", preview_content, height=200, key=f"preview_{i}")
                    
                    # 下载按钮
                    file_extension = {
                        'markdown': 'md',
                        'html': 'html',
                        'json': 'json',
                        'text': 'txt'
                    }.get(result['format'], 'txt')
                    
                    download_filename = f"{result['filename'].rsplit('.', 1)[0]}.{file_extension}"
                    
                    st.download_button(
                        label=f"📥 下载 {result['format'].upper()} 文件",
                        data=result['content'],
                        file_name=download_filename,
                        mime=f"text/{file_extension}",
                        key=f"download_{i}"
                    )
                    
                else:
                    processing_time = result.get('processing_time', 0)
                    st.markdown(f"""
                    <div class="error-box">
                        <strong>❌ 转换失败</strong><br>
                        错误信息: {result['message']}<br>
                        耗时: {processing_time:.1f} 秒
                    </div>
                    """, unsafe_allow_html=True)
        
        # 批量下载
        if success_count > 1:
            st.subheader("📦 批量下载")
            
            # 创建ZIP文件数据
            try:
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for result in results:
                        if result['status'] == 'success':
                            file_extension = {
                                'markdown': 'md',
                                'html': 'html',
                                'json': 'json',
                                'text': 'txt'
                            }.get(result['format'], 'txt')
                            
                            filename = f"{result['filename'].rsplit('.', 1)[0]}.{file_extension}"
                            zip_file.writestr(filename, result['content'])
                
                zip_buffer.seek(0)
                zip_data = zip_buffer.getvalue()
                
                # 显示批量下载按钮
                st.download_button(
                    label="📥 下载所有成功转换的文件 (ZIP)",
                    data=zip_data,
                    file_name="docling_converted_files.zip",
                    mime="application/zip",
                    key="batch_download"
                )
                
                # 显示ZIP文件信息
                st.info(f"📦 ZIP文件包含 {success_count} 个成功转换的文件")
                
            except Exception as e:
                st.error(f"创建批量下载时发生错误: {str(e)}")


if __name__ == "__main__":
    main()