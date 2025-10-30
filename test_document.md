# 测试文档

这是一个用于测试 Docling 可视化界面的示例文档。

## 功能特性

- **多格式支持**：支持 PDF、Word、Excel 等多种格式
- **智能解析**：高级 PDF 理解和 OCR 识别
- **批量处理**：可以同时处理多个文件

## 表格示例

| 功能 | 状态 | 说明 |
|------|------|------|
| 文件上传 | ✅ | 支持多文件上传 |
| 格式转换 | ✅ | 支持多种输出格式 |
| 结果预览 | ✅ | 实时预览转换结果 |

## 代码示例

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("document.pdf")
markdown_content = result.document.export_to_markdown()
```

## 总结

这个界面提供了友好的图形化操作方式，让用户可以轻松使用 Docling 的强大功能。