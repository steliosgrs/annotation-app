# annotation-app
An app to annotate videos for drowsiness detection problem
## Create a virtual environment
```bash
python -m venv venv

# or

conda create --name venv
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