import matplotlib.pyplot as plt
import numpy as np
from train_model import train_model

def plot_training_history(history1, history2):
    # 合并两个阶段的训练历史
    acc = history1.history['accuracy'] + history2.history['accuracy']
    val_acc = history1.history['val_accuracy'] + history2.history['val_accuracy']
    loss = history1.history['loss'] + history2.history['loss']
    val_loss = history1.history['val_loss'] + history2.history['val_loss']
    
    epochs_range = range(1, len(acc) + 1)
    
    # 创建图表
    plt.figure(figsize=(15, 5))
    
    # 绘制准确率
    plt.subplot(1, 2, 1)
    plt.plot(epochs_range, acc, label='Training Accuracy')
    plt.plot(epochs_range, val_acc, label='Validation Accuracy')
    plt.axvline(x=20, color='r', linestyle='--', label='Fine Tuning Start')
    plt.title('Training and Validation Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend(loc='lower right')
    
    # 绘制损失
    plt.subplot(1, 2, 2)
    plt.plot(epochs_range, loss, label='Training Loss')
    plt.plot(epochs_range, val_loss, label='Validation Loss')
    plt.axvline(x=20, color='r', linestyle='--', label='Fine Tuning Start')
    plt.title('Training and Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend(loc='upper right')
    
    plt.tight_layout()
    plt.savefig('training_history.png')
    plt.close()

if __name__ == '__main__':
    # 训练模型并获取历史记录
    history1, history2 = train_model()
    
    # 绘制训练历史
    plot_training_history(history1, history2)
    print("Training visualization saved as 'training_history.png'") 