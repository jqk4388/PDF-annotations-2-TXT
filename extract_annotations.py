import fitz  # PyMuPDF  
import json  
import os  
from tkinter import Tk  
from tkinter.filedialog import askopenfilename  
  
def rect_to_percentage(rect, page_width, page_height):  
    return [  
        rect.x0 / page_width,  
        rect.y0 / page_height  
    ]  
  
import fitz  # 确保导入了 fitz 库

def extract_annotations(pdf_path):
    document = fitz.open(pdf_path)
    annotations = []

    for page_num in range(len(document)):
        page = document.load_page(page_num)
        annot_list = page.annots()
        page_width = page.rect.width
        page_height = page.rect.height

        for annot in annot_list:
            annot_info = {
                "page": page_num + 1,
                "type": annot.type[0],  # Annotation type
                "content": annot.info.get("content", ""),  # Annotation content
                "coordinates_percentage": rect_to_percentage(annot.rect, page_width, page_height),  # Annotation coordinates as percentage
                "creation_date": annot.info.get("creationDate", ""),  # Annotation creation date
                "rect": annot.rect  # 记录矩形框，用于后续排序
            }
            annotations.append(annot_info)

    # 先按页排序
    annotations.sort(key=lambda x: x["page"])

    # 处理排序
    sorted_annotations = []
    current_page = None

    for annot in annotations:
        if annot["page"] != current_page:
            if current_page is not None:
                # 处理上一页的注释
                sorted_annotations.extend(sorted_page_annotations)
            current_page = annot["page"]
            sorted_page_annotations = []  # 重置当前页的注释列表

        sorted_page_annotations.append(annot)

    # 处理最后一页的注释
    if sorted_page_annotations:
        sorted_annotations.extend(sorted_page_annotations)

    # 在每一页中分割为10个区域并进行排序
    final_sorted_annotations = []
    for page_num in range(1, len(document) + 1):
        page_annotations = [annot for annot in sorted_annotations if annot["page"] == page_num]

        # 将页面高度分割成？个区域
        region_height = page_height / 3
        regions = [[] for _ in range(3)]

        # 将注释放入相应的区域
        for annot in page_annotations:
            annot_y = annot["rect"].y0
            region_index = min(int(annot_y // region_height), 9)  # 确保不越界
            regions[region_index].append(annot)

        # 在每个区域内进行排序
        for region in regions:
            # 先按创建时间排序，再按位置从右往左排序，最后按位置从上到下排序
            region.sort(key=lambda x: (x["creation_date"], -x["rect"].x0, x["rect"].y0))
            # 给每个注释添加编号
            for i, sorted_annot in enumerate(region):
                sorted_annot["index"] = i + 1  # 编号从 1 开始
            final_sorted_annotations.extend(region)

    return final_sorted_annotations


  
# def annotations_to_json(annotations, output_path):  
#     with open(output_path, 'w', encoding='utf-8') as f:  
#         json.dump(annotations, f, ensure_ascii=False, indent=4)          
  
def annotations_to_txt(annotations, output_path):  
    with open(output_path, 'w', encoding='utf-8') as f: 
        current_page = None  
        for annot in annotations:  
            if annot['page'] != current_page:  
                if current_page is not None:  
                    f.write("\n")  
                f.write(f"P{annot['page']}\n")  
                current_page = annot['page']  
            f.write(f"{annot['content']}\n\n")  

# 转换列表到labelplus_txt

def format_data(annotations):
    """格式化单个标注"""
    formatted = f"\n----------------[{annotations['index']}]----------------[{annotations['coordinates_percentage'][0]},{annotations['coordinates_percentage'][1]},1]\n{annotations['content']}"
    return formatted

def convert_list_to_lptxt(output_lptxt_path):      
    """将格式化后的数据写入文件"""
    with open(output_lptxt_path, 'w', encoding='utf-8') as file:
        # 写入文件头
        file.write(f"1,0\n-\n框内\n框外\n-")
        current_page = None  
        for annot in annotations:  
            if annot['page'] != current_page:  
                file.write(f"\n>>>>>>>>[{annot['page']:03d}.tif]<<<<<<<<")  
                current_page = annot['page']  
            formatted_data = format_data(annot)
            file.write(formatted_data)

    print(f"转换完成，输出已保存到 {output_lptxt_path} 文件中。")  
    

if __name__ == "__main__":  
    # 创建一个隐藏的Tkinter根窗口  
    root = Tk()  
    root.withdraw()  # 隐藏Tkinter根窗口  
  
    # 弹出文件选择对话框  
    pdf_path = askopenfilename(  
        title="选择一个PDF文件",  
        filetypes=[("PDF文件", "*.pdf")]  
    )  
  
    if pdf_path:  
        # 获取PDF文件的目录和文件名（不带扩展名）  
        pdf_dir = os.path.dirname(pdf_path)  
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]  
  
        # # 构建JSON文件的路径  
        # output_json_path = os.path.join(pdf_dir, f"{pdf_name}.json")  
        # 构建TXT文件的路径  
        output_txt_path = os.path.join(pdf_dir, f"{pdf_name}.txt")  
        # 构建TX文件的路径  
        output_txt_labelplus_path = os.path.join(pdf_dir, f"{pdf_name}_lp.txt")  
  
        annotations = extract_annotations(pdf_path)
        # annotations_to_json(annotations, output_json_path) 
        
        # 生成可读的txt
        annotations_to_txt(annotations, output_txt_path)
        # 生成labelplus格式的txt
        convert_list_to_lptxt(output_txt_labelplus_path)  
  
        print(f"Annotations extracted and saved to {output_txt_labelplus_path} and {output_txt_path}")  
    else:  
        print("没有选择PDF文件")  
  
# input('\n完成！')  
