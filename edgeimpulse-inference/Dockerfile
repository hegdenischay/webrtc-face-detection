#FROM balenalib/%%BALENA-MACHINE-NAME%%-node:build
FROM balenalib/intel-nuc-node:latest

# Install build tools and remove layer cache afterwards
#RUN install_packages git python make gcc g++ libvips-dev
# Install dependencies
RUN apt-get update && apt-get upgrade &&\
  apt-get install build-essential python3 python3-dev && \
  apt-get install -yq unzip \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

EXPOSE 8080

# Switch to working directory for our app
WORKDIR /usr/src/app

# Copies the package.json first for better cache on later pushes
COPY ./app/package.json /usr/src/app/

# Install dependencies
RUN JOBS=MAX npm install --build-from-source && rm -rf /tmp/*

# Copy all the source code in.
COPY ./app/ /usr/src/app/

# Launch our binary on container startup.
CMD ["npm", "start"]
