#To Run the machine after building it (the app runs by default)
docker rm -f extractor

#for running local in chess' dev env 
#docker run --name extractor -p 80:8080 -v ~/.aws:/root/.aws -v  $(pwd)/env.cfg:/extractor/env.cfg -d local/extractor:latest 

#docker run --name extractor -p 80:8080 -v `pwd`/env.cfg:/extractor/env.cfg -v ~/.aws:/root/.aws -v /tmp:/data -d local/extractor:latest
docker run --name extractor -p 3000:8080 -v `pwd`/env.cfg:/extractor/env.cfg -v ~/.aws:/root/.aws -d local/extractor:latest
