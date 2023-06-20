# annotation-app
The annotation app use [SPIGA](https://github.com/andresprados/SPIGA), a **face alignment** and **headpose estimator** a state-of-the-art model to extract 98 landmarks. 

## Create a virtual environment
```bash
conda create --name venv

# or 

python -m venv venv
```
## Install Libraries
```bash
pip install -r requierements.txt
```

## Install Spiga
```bash
git clone https://github.com/andresprados/SPIGA.git
cd spiga
pip install -e .  

# To run the video analyzer demo install the extra requirements.
pip install -e .[demo]
```

## Running the App

To run the app for our case (20 FPS) 
```bash
python app.py
```

### app.py
The main calls the EAR MAR extractor


### ear_mar_app.py

The **ear_mar_extractor()** function is responsible for extracting EAR and MAR from a given path of video directory. 
#### Steps
1) Reads a path
2) A Video Reader instantiated and reads the video in segments
3) From every segments calls the **landmarks_per_frame_spiga()** to extract landmarks
4) Then, calculate the EAR & MAR 
