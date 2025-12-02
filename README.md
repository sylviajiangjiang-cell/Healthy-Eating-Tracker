# Healthy Eating Tracker

### 1. **System Requirements**

- Python 3.10
- Windows11

### 2. **Installation Steps**

```
# Clone project files
git clone https://github.com/sylviajiangjiang-cell/Healthy-Eating-Tracker.git

# Enter the project directory
cd health-diet-tracker

# Install dependencies
pip install -r requirements

# Run the application
python app.py
```

### 3. **Access the app**

**After starting, open in the browser:**

```
http://localhost:5000
```



## 📁 **File Structure Description**

```
Healthy-Eating-Tracker/
├── app.py                 # Main application file
├── templates/            # Website template
│   ├── base.html        # Basic Template
│   ├── index.html       # index
│   ├── login.html       # login
│   ├── register.html    # register
│   ├── profile.html     # profile
│   ├── diet_plan.html   # diet_plan
│   ├── nutrition.html   # nutrition
│   ├── error.html       # error
│   ├── 404.html         # 404
│   └── 500.html         # 500
├── static/              # static
│   └── style.css       # style
└── README.md           # Instruction manual
```

## 📊  **Main Features Page**

| **Page**           | **Path**              | **Function Description**                           |
| :----------------- | :-------------------- | :------------------------------------------------- |
| index              | `/`                   | Display personal health overview and visual charts |
| login              | `/login`              | User Login Page                                    |
| register           | `/register`           | New User Registration Page                         |
| profile            | `/profile`            | View and edit personal information                 |
| diet-plan          | `/diet-plan`          | View personalized meal plan                        |
| nutrition analysis | `/nutrition-analysis` | Analyze food nutrition components                  |