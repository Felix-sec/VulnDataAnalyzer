import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import re
from pathlib import Path
import pandas as pd
from keyword_manager import KeywordManager
from keyword_dialog import KeywordDialog
from tkinterdnd2 import TkinterDnD, DND_FILES

class JsonExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("漏扫数据分析工具 - By Felix")
        self.root.geometry("800x600")
        
        # 创建标签页
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建漏洞分类标签页
        self.vuln_class_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.vuln_class_frame, text="漏洞类型分类")
        
        # 创建IP提取标签页
        self.ip_extract_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.ip_extract_frame, text="漏洞明细表格IP提取")
        
        # 在漏洞分类标签页中添加组件
        # 输入文件框
        self.input_frame = tk.LabelFrame(self.vuln_class_frame, text="输入HTML文件", padx=10, pady=5)
        self.input_frame.pack(fill="x", padx=10, pady=5)
        
        self.input_path = tk.StringVar()
        self.input_entry = tk.Entry(self.input_frame, textvariable=self.input_path, width=80)
        self.input_entry.pack(side="left", padx=5)
        
        self.browse_btn = tk.Button(self.input_frame, text="浏览", command=self.browse_input)
        self.browse_btn.pack(side="left", padx=5)
        
        # 拖放提示移到输入框右边
        self.drop_label = tk.Label(self.input_frame, text="(支持拖放HTML文件)", pady=5)
        self.drop_label.pack(side="left", padx=5)
        
        # 输出文件框
        self.output_frame = tk.LabelFrame(self.vuln_class_frame, text="输出JSON文件", padx=10, pady=5)
        self.output_frame.pack(fill="x", padx=10, pady=5)
        
        self.output_path = tk.StringVar()
        self.output_entry = tk.Entry(self.output_frame, textvariable=self.output_path, width=80)
        self.output_entry.pack(side="left", padx=5)
        
        self.save_btn = tk.Button(self.output_frame, text="浏览", command=self.browse_output)
        self.save_btn.pack(side="left", padx=5)
        
        # 将提取JSON按钮移到输出文件框中
        self.extract_btn = tk.Button(self.output_frame, text="提取JSON", 
                                   command=self.extract_json)
        self.extract_btn.pack(side="left", padx=5)
        
        # 添加关键词管理器
        self.keyword_manager = KeywordManager()
        
        # 创建漏洞分类框架
        vuln_frame = tk.LabelFrame(self.vuln_class_frame, text="漏洞类型分类", padx=5, pady=5)
        vuln_frame.pack(fill="x", padx=10, pady=5)
        
        # 添加匹配模式选择
        self.match_mode = tk.StringVar(value="both")
        match_label = tk.Label(vuln_frame, text="匹配模式:")
        match_label.pack(side="left", padx=5)
        
        modes = [
            ("精准匹配", "exact"),
            ("模糊匹配", "fuzzy"),
            ("精准+模糊", "both")
        ]
        
        for text, mode in modes:
            tk.Radiobutton(vuln_frame, text=text, variable=self.match_mode, 
                          value=mode).pack(side="left", padx=5)
        
        # 添加关键词管理按钮
        self.keyword_btn = tk.Button(vuln_frame, text="关键词管理", 
                                   command=self.show_keyword_dialog)
        self.keyword_btn.pack(side="left", padx=15)
        
        # 添加导出按钮
        self.vuln_btn = tk.Button(vuln_frame, text="导出分类", 
                                 command=self.export_vuln_types)
        self.vuln_btn.pack(side="left", padx=5)
        
        # 日志框
        self.log_frame = tk.LabelFrame(self.vuln_class_frame, text="运行日志", padx=10, pady=5)
        self.log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 创建文本框和滚动条
        self.log_text = tk.Text(self.log_frame, height=15, width=80)
        self.scrollbar = tk.Scrollbar(self.log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.scrollbar.set)
        
        # 放置文本框和滚动条
        self.scrollbar.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)
        
        # 状态显示
        self.status_var = tk.StringVar()
        self.status_label = tk.Label(self.vuln_class_frame, textvariable=self.status_var)
        self.status_label.pack(pady=5)
        
        # 绑定拖放事件
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)
        
        # 初始化IP提取标签页
        self.init_ip_extract_tab()

    def log_message(self, message, level="INFO"):
        """添加日志消息到日志框"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] [{level}] {message}\n")
        self.log_text.see("end")  # 自动滚动到最新消息
        
    def browse_input(self):
        filename = filedialog.askopenfilename(
            filetypes=[("HTML文件", "*.html"), ("所有文件", "*.*")]
        )
        if filename:
            self.input_path.set(filename)
            # 自动设置输出文件名
            output_path = Path(filename).with_suffix('.json')
            self.output_path.set(str(output_path))

    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if filename:
            self.output_path.set(filename)

    def browse_ip_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        if filename:
            self.ip_file_path_var.set(filename)

    def handle_drop(self, event):
        file_path = event.data
        self.log_message(f"收到拖放文件: {file_path}")
        
        # 移除花括号并转换为Path对象
        file_path = Path(file_path.strip('{}'))
        
        # 检查文件扩展名（不区分大小写）
        if file_path.suffix.lower() in ('.html', '.htm'):
            self.input_path.set(str(file_path))
            output_path = file_path.with_suffix('.json')
            self.output_path.set(str(output_path))
            self.log_message(f"已设置输入文件: {file_path}")
            self.log_message(f"已设置输出文件: {output_path}")
        else:
            self.log_message(f"无效的文件类型: {file_path}", "ERROR")

    def handle_ip_file_drop(self, event):
        file_path = event.data
        self.log_message(f"收到拖放文件: {file_path}")
        
        # 移除花括号并转换为Path对象
        file_path = Path(file_path.strip('{}'))
        
        # 检查文件扩展名（不区分大小写）
        if file_path.suffix.lower() == '.xlsx':
            self.ip_file_path_var.set(str(file_path))
            self.log_message(f"已设置IP提取Excel文件: {file_path}")
        else:
            self.log_message(f"无效的文件类型: {file_path}", "ERROR")

    def extract_json(self):
        input_file = self.input_path.get()
        output_file = self.output_path.get()
        
        if not input_file or not output_file:
            self.log_message("请选择输入和输出文件！", "ERROR")
            return
            
        try:
            # 尝试多种编码格式
            encodings = ['utf-8', 'gbk', 'gb2312', 'iso-8859-1']
            file_content = None
            
            for encoding in encodings:
                try:
                    with open(input_file, encoding=encoding) as f:
                        file_content = f.read()
                    self.log_message(f"成功使用 {encoding} 编码读取文件")
                    break
                except UnicodeDecodeError:
                    continue
            
            if file_content is None:
                self.log_message(f"无法读取文件，已尝试以下编码: {', '.join(encodings)}", "ERROR")
                return
            
            self.log_message(f"正在处理文件: {input_file}")
            pat_list = re.findall(r'<script>window.data = (.*?);</script>', file_content)
            
            if not pat_list:
                self.log_message("未在HTML文件中找到匹配的JSON数据！", "ERROR")
                return
                
            data_json = json.loads(pat_list[0])
            
            with open(output_file, 'w', encoding='utf8') as f:
                json.dump(data_json, f, ensure_ascii=False, indent=4)
                
            success_msg = f"JSON数据已成功保存到: {output_file}"
            self.log_message(success_msg, "SUCCESS")
            self.status_var.set("JSON提取成功！")
            
        except Exception as e:
            error_msg = f"处理过程中出现错误：{str(e)}"
            self.log_message(error_msg, "ERROR")
            self.status_var.set(f"错误: {str(e)}")

    def show_keyword_dialog(self):
        KeywordDialog(self.root, self.keyword_manager)
    
    def export_vuln_types(self):
        try:
            # 先让用户选择保存位置
            output_excel = filedialog.asksaveasfilename(
                title="保存漏洞分类Excel",
                defaultextension=".xlsx",
                initialfile="漏洞类型分类.xlsx",
                filetypes=[
                    ("Excel文件", "*.xlsx"),
                    ("所有文件", "*.*")
                ]
            )
            
            if not output_excel:  # 用户取消选择
                return
            
            # 读取JSON文件
            with open(self.output_path.get(), 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 获取漏洞列表
            vuln_list = data['categories'][3]['children'][0]['data']['vulns_info']['vuln_distribution']['vuln_list']
            
            # 准备Excel数据
            excel_data = []
            for i, vuln in enumerate(vuln_list, 1):
                # 处理描述和解决方案
                description = '\n'.join(filter(None, vuln.get('i18n_description', [])))
                solution = '\n'.join(filter(None, vuln.get('i18n_solution', [])))
                
                # 获取漏洞等级中文
                level_map = {'high': '高危', 'middle': '中危', 'low': '低危'}
                level = level_map.get(vuln.get('vuln_level', ''), '未知')
                
                # 获取漏洞类型
                vuln_type = self.keyword_manager.get_type(
                    vuln.get('i18n_name', ''), 
                    self.match_mode.get()
                )
                
                excel_data.append({
                    '序号': i,
                    '漏洞名称': vuln.get('i18n_name', ''),
                    '类型': vuln_type,
                    '漏洞等级': level,
                    '影响主机个数': vuln.get('vuln_count', 0),
                    '受影响主机': vuln.get('target', ''),
                    '详细描述': description,
                    '解决办法': solution
                })
            
            # 创建DataFrame并导出到Excel
            df = pd.DataFrame(excel_data)
            df.to_excel(output_excel, index=False)
            
            self.log_message(f"漏洞类型分类已导出到: {output_excel}", "SUCCESS")
            
        except Exception as e:
            self.log_message(f"导出漏洞类型分类时出错: {str(e)}", "ERROR")

    def init_ip_extract_tab(self):
        # 添加说明文字
        description = "本功能旨在漏洞明细Excel表格按漏洞等级、漏洞类型进行提取IP地址，支持IP去重，请先将漏洞明细Excel表格进行漏洞分类后再使用本功能！"
        desc_label = tk.Label(self.ip_extract_frame, text=description, wraplength=700, justify="left")
        desc_label.pack(fill="x", padx=10, pady=10)
        
        # 文件选择框架
        file_frame = tk.LabelFrame(self.ip_extract_frame, text="选择Excel文件", padx=10, pady=5)
        file_frame.pack(fill="x", padx=10, pady=5)
        
        self.ip_file_path_var = tk.StringVar()
        self.ip_file_entry = tk.Entry(file_frame, textvariable=self.ip_file_path_var, width=80)
        self.ip_file_entry.pack(side="left", padx=5)
        
        browse_btn = tk.Button(file_frame, text="浏览", command=self.browse_ip_file)
        browse_btn.pack(side="left", padx=5)
        
        # Excel类型选择框架
        type_frame = tk.LabelFrame(self.ip_extract_frame, text="Excel类型", padx=10, pady=5)
        type_frame.pack(fill="x", padx=10, pady=5)
        
        self.excel_type_var = tk.StringVar(value="complex")
        simple_radio = tk.Radiobutton(type_frame, text="简单表格(一列一个字段)", 
                                     variable=self.excel_type_var, value="simple")
        simple_radio.pack(side="left", padx=5)
        complex_radio = tk.Radiobutton(type_frame, text="复杂表格(混合布局字段)", 
                                      variable=self.excel_type_var, value="complex")
        complex_radio.pack(side="left", padx=5)
        
        # 去重选项
        self.ip_deduplicate_var = tk.BooleanVar()
        dedup_check = tk.Checkbutton(self.ip_extract_frame, text="去重IP地址", 
                                   variable=self.ip_deduplicate_var)
        dedup_check.pack(pady=10)
        
        # 提取按钮
        extract_btn = tk.Button(self.ip_extract_frame, text="提取IP地址", 
                              command=self.extract_ip_addresses)
        extract_btn.pack(pady=10)
        
        # IP提取状态标签
        self.ip_status_var = tk.StringVar()
        ip_status_label = tk.Label(self.ip_extract_frame, 
                                 textvariable=self.ip_status_var, fg="green")
        ip_status_label.pack(pady=5)
        
        # 文件拖放支持
        self.ip_file_entry.drop_target_register(DND_FILES)
        self.ip_file_entry.dnd_bind('<<Drop>>', self.handle_ip_file_drop)

    def extract_ip_addresses(self):
        file_path = self.ip_file_path_var.get()
        if not file_path:
            messagebox.showwarning("警告", "请选择一个有效的Excel文件。")
            return

        # 让用户选择导出目录
        output_dir = filedialog.askdirectory(title="选择IP地址文件保存目录")
        if not output_dir:  # 用户取消选择
            return

        try:
            df = pd.read_excel(file_path)
            
            # 初始化文件句柄字典和IP集合字典
            file_handles = {}
            ip_sets = {}
            
            if self.excel_type_var.get() == "simple":
                # 处理简单表格格式
                for _, row in df.iterrows():
                    risk_level = str(row['漏洞等级']).strip()
                    category = str(row['类型']).strip()
                    ip_addresses = str(row['受影响主机']).strip()
                    
                    if ip_addresses and ip_addresses != 'nan':
                        # 构建完整的文件路径
                        filename = Path(output_dir) / f"{risk_level}-{category}.txt"
                        
                        # 如果文件句柄不存在，则创建新的文件句柄和IP集合
                        if filename not in file_handles:
                            file_handles[filename] = open(filename, 'w', encoding='utf-8')
                            if self.ip_deduplicate_var.get():
                                ip_sets[filename] = set()
                        
                        # 如果有多个IP，使用";"分隔
                        for ip in ip_addresses.split(';'):
                            ip = ip.strip()
                            if ip:
                                if self.ip_deduplicate_var.get():
                                    if ip not in ip_sets[filename]:
                                        file_handles[filename].write(ip + '\n')
                                        ip_sets[filename].add(ip)
                                else:
                                    file_handles[filename].write(ip + '\n')
            else:
                # 处理复杂表格格式
                for i in range(1, len(df), 4):
                    if i + 1 < len(df):
                        risk_level = str(df.iloc[i-1, 2]).strip()
                        category = str(df.iloc[i-1, 4]).strip()
                        
                        # 构建完整的文件路径
                        filename = Path(output_dir) / f"{risk_level}-{category}.txt"
                        
                        # 如果文件句柄不存在，则创建新的文件句柄和IP集合
                        if filename not in file_handles:
                            file_handles[filename] = open(filename, 'w', encoding='utf-8')
                            if self.ip_deduplicate_var.get():
                                ip_sets[filename] = set()
                        
                        ip_addresses = str(df.iloc[i, 3]).strip()
                        if ip_addresses and ip_addresses != 'nan':
                            # 如果有多个IP，使用";"分隔
                            for ip in ip_addresses.split(';'):
                                ip = ip.strip()
                                if ip:
                                    if self.ip_deduplicate_var.get():
                                        if ip not in ip_sets[filename]:
                                            file_handles[filename].write(ip + '\n')
                                            ip_sets[filename].add(ip)
                                    else:
                                        file_handles[filename].write(ip + '\n')
            
            # 确保所有文件都被正确关闭
            for fh in file_handles.values():
                fh.close()
            
            self.ip_status_var.set(f"IP地址已成功提取并保存到目录: {output_dir}")
            messagebox.showinfo("完成", f"IP地址已成功提取并保存到目录: {output_dir}")
        except Exception as e:
            self.ip_status_var.set(f"发生错误: {str(e)}")
            messagebox.showerror("错误", f"发生错误: {str(e)}")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = JsonExtractorGUI(root)
    root.mainloop()