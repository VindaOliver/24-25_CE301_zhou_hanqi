# Cat Breed Recognition System

This project is a web application for cat breed recognition based on deep learning, built using TensorFlow and Flask. The system can identify 20 common cat breeds and provides detailed breed information.

## Features

- **Breed Recognition**: Upload cat photos for identification using a MobileNetV2 deep learning model
- **User Accounts**: Create accounts to save your recognition history
- **Breed Information**: Get detailed info about each cat breed including:
  - Physical characteristics
  - Personality traits
  - Care requirements
  - Origin details
- **History Records**: View, manage, and revisit your past identification results
- **Statistics**: Track your personal usage data and platform-wide stats
- **Daily Recommendations**: Get daily recommended cat breeds to explore
- **Responsive Design**: Works on computers, tablets, and mobile phones

## Supported Cat Breeds

The system can identify these 20 common cat breeds:

- Abyssinian
- American Curl
- American Shorthair
- Bengal
- Birman
- Bombay
- British Shorthair
- Egyptian Mau
- Exotic Shorthair
- Himalayan
- Maine Coon
- Manx
- Munchkin
- Norwegian Forest
- Persian
- Ragdoll
- Russian Blue
- Scottish Fold
- Siamese
- Sphynx

## Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript
- **Backend**: Python 3.8+, Flask framework
- **Database**: MySQL
- **Machine Learning**: TensorFlow 2.x with MobileNetV2 architecture
- **Deployment**: Docker and Docker Compose

## Setup and Installation

### Requirements

- Python 3.8 or higher
- MySQL database
- Docker and Docker Compose (optional, for containerized deployment)

### Database Setup

1. Create a MySQL database:
```sql
CREATE DATABASE cat_breed;
```

2. Configure the database connection in `app.py`:
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'db': 'cat_breed',
    'charset': 'utf8mb4',
    'cursorclass': DictCursor
}
```

### Installation Steps

1. Clone the repository:
```bash
git clone https://cseegit.essex.ac.uk/24-25-ce301/24-25_CE301_zhou_hanqi.git
cd 24-25_CE301_zhou_hanqi
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Access the app: `http://localhost:5000`


## Model Details

- **Architecture**: MobileNetV2 with transfer learning
- **Input Size**: 224×224 pixels (RGB)
- **Training Method**: Two-phase transfer learning:
  - Phase 1: Train only the classification layers
  - Phase 2: Fine-tune the deeper convolutional layers
- **Dataset**: Custom dataset with 20 cat breeds stored in `dataset/train` and `dataset/val` folders

## Training Your Own Model

Use the included training script:
```bash
python train_model.py
```

The script needs data organized like this:
```
dataset/
├── train/
│   ├── Abyssinian/
│   │   ├── image1.jpg
│   │   └── ...
│   ├── Bengal/
│   └── ...
└── val/
    ├── Abyssinian/
    └── ...
```

## Project Structure

- `app.py`: Main application file with all routes and logic
- `train_model.py`: Script for training the cat breed classifier
- `templates/`: HTML templates for the web interface
- `static/`: CSS, JavaScript, and images
- `model/`: Folder for trained models
- `dataset/`: Training and validation images



## Acknowledgments

- TensorFlow and Keras deep learning frameworks
- Flask web framework
- All dataset contributors

