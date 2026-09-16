#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys

def parse_rename_commands(file_path):
    """
    解析重命名命令文件，提取重命名命令
    支持格式: ren "原名称" "新名称"
    可以重命名文件和文件夹
    """
    rename_commands = []
    
    try:
        # 使用 utf-8-sig 自动兼容带 BOM 的 UTF-8 文件
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith('::') or line.startswith('REM') or line.startswith('#'):
                continue
                
            # 匹配 ren 命令
            match = re.match(r'ren\s+"([^"]+)"\s+"([^"]+)"', line, re.IGNORECASE)
            if match:
                old_name = match.group(1)
                new_name = match.group(2)
                rename_commands.append((old_name, new_name, line_num))
            else:
                print(f"警告: 第 {line_num} 行格式不正确，已跳过: {line}")
                
    except UnicodeDecodeError:
        print("错误: 文件编码不是UTF-8，请确保文件使用UTF-8编码保存")
        return None
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return None
        
    return rename_commands

def select_txt_file(txt_files):
    """
    让用户从多个txt文件中选择一个
    """
    print("发现多个txt文件:")
    for i, file in enumerate(txt_files, 1):
        print(f"  {i}. {file}")
    
    while True:
        try:
            choice = input(f"\n请选择要使用的文件 (1-{len(txt_files)}): ").strip()
            if not choice:
                print("请输入选择！")
                continue
                
            choice_num = int(choice)
            if 1 <= choice_num <= len(txt_files):
                return txt_files[choice_num - 1]
            else:
                print(f"请输入 1 到 {len(txt_files)} 之间的数字！")
        except ValueError:
            print("请输入有效的数字！")

def execute_rename_commands():
    """
    执行重命名命令
    支持文件和文件夹重命名
    """
    # ================= 核心修复：强制切换工作目录 =================
    # 获取脚本所在的目录，并切换过去。这样双击运行时就不会停留在 system32 目录
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
    except Exception as e:
        print(f"切换工作目录失败: {e}")
        input("按回车键退出...")
        return
    # ============================================================

    current_dir = os.getcwd()
    print(f"工作目录: {current_dir}")
    print("=" * 50)
    
    # 查找当前目录下的txt文件
    txt_files = []
    for file in os.listdir('.'):
        if file.lower().endswith('.txt'):
            txt_files.append(file)
    
    if not txt_files:
        print("未找到任何txt文件！")
        print("请创建一个包含重命名命令的txt文件")
        print("命令格式: ren \"原名称\" \"新名称\"")
        input("按回车键退出...")
        return
    
    # 如果有多个txt文件，优先选择 Rename.txt，否则让用户选择
    if 'Rename.txt' in txt_files:
        txt_file = 'Rename.txt'
        print(f"自动选择文件: {txt_file}")
    elif len(txt_files) > 1:
        txt_file = select_txt_file(txt_files)
    else:
        txt_file = txt_files[0]
    
    print(f"读取文件: {txt_file}")
    print("=" * 50)
    
    # 解析文件
    commands = parse_rename_commands(txt_file)
    if commands is None:
        input("按回车键退出...")
        return
    
    if not commands:
        print(f"文件 '{txt_file}' 中没有找到有效的重命名命令！")
        input("按回车键退出...")
        return
    
    print(f"找到 {len(commands)} 个重命名命令:")
    print("=" * 50)
    
    # 检查文件/文件夹是否存在并显示重命名计划
    rename_plan = []
    missing_items = []
    
    for old_name, new_name, line_num in commands:
        if os.path.exists(old_name):
            # 判断是文件还是文件夹
            item_type = "文件夹" if os.path.isdir(old_name) else "文件"
            rename_plan.append((old_name, new_name, line_num, item_type))
            print(f"第 {line_num:2d} 行: [{item_type}] {old_name}")
            print(f"        -> {new_name}")
        else:
            missing_items.append((old_name, line_num))
            print(f"第 {line_num:2d} 行: {old_name} [不存在]")
            print(f"        -> {new_name}")
        print()
    
    # 显示缺失警告
    if missing_items:
        print("警告: 以下项目不存在，将跳过这些重命名命令:")
        for old_name, line_num in missing_items:
            print(f"  第 {line_num} 行: {old_name}")
        print()
    
    if not rename_plan:
        print("没有可执行的重命名操作！")
        input("按回车键退出...")
        return
    
    # 直接执行重命名，无需确认
    print("开始执行重命名...")
    print("-" * 50)
    
    success_count = 0
    failed_count = 0
    
    for old_name, new_name, line_num, item_type in rename_plan:
        try:
            # 检查目标是否已存在
            if os.path.exists(new_name):
                print(f"第 {line_num} 行: 目标{item_type}已存在，跳过 - {new_name}")
                failed_count += 1
                continue
                
            os.rename(old_name, new_name)
            print(f"第 {line_num} 行: ✓ 成功 [{item_type}] - {old_name} -> {new_name}")
            success_count += 1
        except Exception as e:
            print(f"第 {line_num} 行: ✗ 失败 [{item_type}] - {old_name} -> {new_name} (错误: {e})")
            failed_count += 1
    
    print("=" * 50)
    print(f"重命名完成！成功: {success_count}, 失败: {failed_count}")
    input("按回车键退出...")

if __name__ == "__main__":
    execute_rename_commands()
