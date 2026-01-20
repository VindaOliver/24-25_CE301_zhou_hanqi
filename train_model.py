import os
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
import matplotlib.pyplot as plt
import pickle
from datetime import datetime
import numpy as np

# 配置参数
IMAGE_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 50
LEARNING_RATE = 0.0001
TRAIN_DIR = 'dataset/train'
VAL_DIR = 'dataset/val'

# 创建保存目录
os.makedirs('model', exist_ok=True)
os.makedirs('training_history', exist_ok=True)

def create_model(num_classes):
    print(f"\n创建模型 (num_classes={num_classes})...")
    # 加载预训练的MobileNetV2模型
    base_model = MobileNetV2(
        weights='imagenet',
        include_top=False,
        input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3)
    )
    print("已加载预训练的 MobileNetV2 模型")
    
    # 冻结基础模型层
    base_model.trainable = False
    print("已冻结基础模型层")
    
    # 添加自定义顶层
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(1024, activation='relu')(x)
    x = Dropout(0.5)(x)
    x = BatchNormalization()(x)
    predictions = Dense(num_classes, activation='softmax')(x)
    
    model = Model(inputs=base_model.input, outputs=predictions)
    print("模型创建完成")
    return model, base_model

def setup_data_generators():
    print("\n设置数据生成器...")
    # 数据增强配置
    train_datagen = ImageDataGenerator(
        preprocessing_function=tf.keras.applications.mobilenet_v2.preprocess_input,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest'
    )

    val_datagen = ImageDataGenerator(
        preprocessing_function=tf.keras.applications.mobilenet_v2.preprocess_input
    )

    print("正在加载训练数据...")
    train_generator = train_datagen.flow_from_directory(
        TRAIN_DIR,
        target_size=(IMAGE_SIZE, IMAGE_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical'
    )

    print("正在加载验证数据...")
    val_generator = val_datagen.flow_from_directory(
        VAL_DIR,
        target_size=(IMAGE_SIZE, IMAGE_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical'
    )

    return train_generator, val_generator

def plot_training_history(history, timestamp):
    # 绘制准确率曲线
    plt.figure(figsize=(10, 6))
    plt.plot(history.history['accuracy'], label='Training Accuracy')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
    plt.title('Model Accuracy over Epochs')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend(loc='lower right')
    plt.grid(True)
    plt.savefig(f'training_history/accuracy_plot_{timestamp}.png')
    plt.close()

    # 绘制损失值曲线
    plt.figure(figsize=(10, 6))
    plt.plot(history.history['loss'], label='Training Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.title('Model Loss over Epochs')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend(loc='upper right')
    plt.grid(True)
    plt.savefig(f'training_history/loss_plot_{timestamp}.png')
    plt.close()

def train_model():
    print("\n开始训练过程...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 设置数据生成器
    train_generator, val_generator = setup_data_generators()
    num_classes = len(train_generator.class_indices)
    print(f"检测到的类别数量: {num_classes}")
    print("类别映射:", train_generator.class_indices)
    
    # 创建模型
    model, base_model = create_model(num_classes)
    
    # 定义回调函数
    callbacks = [
        ModelCheckpoint(
            f'model/best_model_{timestamp}.h5',
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1
        ),
        EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True,
            verbose=1
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.1,
            patience=5,
            min_lr=1e-6,
            verbose=1
        )
    ]
    
    # 第一阶段：训练顶层
    print("\n第一阶段：训练顶层...")
    model.compile(
        optimizer=Adam(learning_rate=LEARNING_RATE),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    history1 = model.fit(
        train_generator,
        steps_per_epoch=train_generator.samples // BATCH_SIZE,
        epochs=20,
        validation_data=val_generator,
        validation_steps=val_generator.samples // BATCH_SIZE,
        callbacks=callbacks
    )
    
    # 第二阶段：微调最后几层
    print("\n第二阶段：微调最后几层...")
    # 解冻最后50层
    for layer in base_model.layers[-50:]:
        layer.trainable = True
    print("已解冻最后50层")
    
    model.compile(
        optimizer=Adam(learning_rate=LEARNING_RATE/10),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    history2 = model.fit(
        train_generator,
        steps_per_epoch=train_generator.samples // BATCH_SIZE,
        epochs=EPOCHS,
        validation_data=val_generator,
        validation_steps=val_generator.samples // BATCH_SIZE,
        callbacks=callbacks
    )
    
    # 合并两个阶段的训练历史
    combined_history = {
        'accuracy': history1.history['accuracy'] + history2.history['accuracy'],
        'val_accuracy': history1.history['val_accuracy'] + history2.history['val_accuracy'],
        'loss': history1.history['loss'] + history2.history['loss'],
        'val_loss': history1.history['val_loss'] + history2.history['val_loss']
    }
    
    # 保存训练历史
    history_file = f'training_history/history_{timestamp}.pkl'
    with open(history_file, 'wb') as f:
        pickle.dump(combined_history, f)
    print(f"训练历史已保存到: {history_file}")
    
    # 绘制训练历史图表
    plot_training_history(type('History', (), {'history': combined_history})(), timestamp)
    
    # 保存最终模型
    final_model_path = f'model/final_model_{timestamp}.h5'
    model.save(final_model_path)
    print(f"最终模型已保存到: {final_model_path}")
    
    return combined_history

if __name__ == '__main__':
    # 检查数据集目录
    if not os.path.exists(TRAIN_DIR) or not os.path.exists(VAL_DIR):
        print(f"""
请按以下结构组织数据集：

dataset/
├── train/
│   ├── Abyssinian/
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   └── ...
│   ├── Bengal/
│   │   └── ...
│   └── ...
└── val/
    ├── Abyssinian/
    │   └── ...
    ├── Bengal/
    │   └── ...
    └── ...
        """)
    else:
        print("开始训练过程...")
        train_model() 