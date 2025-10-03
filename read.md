#Backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate   
pip install -r automationtool/requirements.txt
cd automationtool
python app.py

#Frontend
npm install
npm start

#DOCKERHUB
docker build -t aksharshare/makereels-frontend:latest ./frontend
docker push aksharshare/makereels-frontend:latest
docker build -t aksharshare/makereels-backend:latest ./automationtool
docker push aksharshare/makereels-backend:latest

#VPS 
sudo apt update
sudo apt install certbot
sudo certbot certonly --standalone -d makereels.live -d www.makereels.live
sudo ls -la /etc/letsencrypt/live/makereels.live/

docker logs makereels-frontend
docker logs makereels-backend
docker exec makereels-backend tail -f /app/pipeline.log
docker exec makereels-backend cat /app/master.log
docker exec makereels-backend tail -f /app/master.log