import os
import shutil
import random
from pathlib import Path

# 设置随机种子以确保结果可重现
random.seed(42)

# 源数据集目录
dataset_dir = Path('dataset')

# 训练集和验证集的比例
TRAIN_RATIO = 0.8

def split_dataset():
    # 获取所有品种目录
    breed_dirs = [d for d in dataset_dir.iterdir() if d.is_dir() and d.name not in ['train', 'val']]
    
    for breed_dir in breed_dirs:
        print(f"Processing {breed_dir.name}...")
        
        # 创建目标目录
        train_breed_dir = dataset_dir / 'train' / breed_dir.name
        val_breed_dir = dataset_dir / 'val' / breed_dir.name
        train_breed_dir.mkdir(parents=True, exist_ok=True)
        val_breed_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取所有图片文件
        image_files = list(breed_dir.glob('*.*'))
        random.shuffle(image_files)
        
        # 计算分割点
        split_idx = int(len(image_files) * TRAIN_RATIO)
        
        # 分割数据集
        train_files = image_files[:split_idx]
        val_files = image_files[split_idx:]
        
        # 移动文件到对应目录
        for file in train_files:
            shutil.copy2(file, train_breed_dir / file.name)
        
        for file in val_files:
            shutil.copy2(file, val_breed_dir / file.name)
        
        print(f"  - Training images: {len(train_files)}")
        print(f"  - Validation images: {len(val_files)}")

if __name__ == '__main__':
    split_dataset()
    print("\nDataset split completed!") 