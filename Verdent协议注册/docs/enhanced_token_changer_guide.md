# Verdent Token 更改器增强版使用指南

## 新增功能概述

此增强版在原有Token管理功能基础上，新增了系统级管理功能，包括：
- 自动修改系统机器码（MachineGuid）
- 自动重启Verdent软件
- 机器码备份与还原功能

## 安装依赖

```bash
pip install -r requirements.txt
```

或手动安装：
```bash
pip install psutil pywin32
```

## 主要功能

### 1. 程序启动时自动操作

当程序以**管理员权限**启动时，会自动执行以下操作：
1. **备份原始机器码** - 保存系统初始的MachineGuid
2. **生成新机器码** - 创建一个随机的UUID作为新的机器码
3. **修改注册表** - 更新系统注册表中的MachineGuid
4. **重启Verdent** - 自动关闭并重新启动Verdent软件

### 2. 系统管理功能

#### 重启 Verdent
- 终止所有Verdent进程
- 自动查找并启动Verdent应用

#### 更换机器码
- 生成新的随机机器码
- 备份当前机器码
- 更新注册表设置

#### 还原机器码
- 恢复到系统原始的机器码
- 从备份文件读取原始值
- 更新注册表设置

#### 查看机器码
- 显示当前使用的机器码
- 显示原始备份的机器码
- 显示修改历史记录

## 重要说明

### 管理员权限
- **必须**以管理员权限运行程序才能修改注册表
- 程序启动时会自动检测权限并提示提升

### 机器码备份
- 备份文件：`machine_guid_backup.json`
- 位置：程序运行目录
- 内容：原始机器码、修改历史、时间戳

### 注册表位置
```
HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Cryptography\MachineGuid
```

## 使用场景

1. **初次使用**
   - 程序启动时自动完成所有初始化
   - 无需手动操作

2. **需要多个机器码**
   - 使用"更换机器码"功能生成新的ID
   - 每次更换都会记录在备份文件中

3. **恢复原始状态**
   - 使用"还原机器码"恢复到初始值
   - 适用于卸载程序或恢复系统

## 注意事项

⚠️ **警告**：修改MachineGuid可能影响某些依赖此值的软件或服务
⚠️ **建议**：在修改前确保了解可能的影响
⚠️ **备份**：始终保留`machine_guid_backup.json`文件

## 故障排除

### 权限问题
- 确保以管理员身份运行
- Windows UAC可能需要确认

### Verdent无法启动
- 检查Verdent安装路径
- 手动从开始菜单启动

### 机器码无法修改
- 检查是否有安全软件阻止
- 确认管理员权限

## 文件结构

```
token_changer_gui.py      # 主程序（增强版）
requirements.txt          # 依赖列表
machine_guid_backup.json  # 机器码备份文件（自动生成）
docs/
  └── enhanced_token_changer_guide.md  # 本文档
```
