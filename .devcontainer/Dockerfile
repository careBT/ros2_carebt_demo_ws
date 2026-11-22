FROM althack/ros2:kilted-full

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
   && apt-get -y install --no-install-recommends \
   ros-kilted-navigation2 \
   ros-kilted-nav2-bringup \
   ros-kilted-ackermann-msgs \
   ros-kilted-marker-msgs \
   ros-kilted-teleop-twist-keyboard \
   ros-kilted-rclpy-message-converter \
   #
   # Clean up
   && apt-get autoremove -y \
   && apt-get clean -y \
   && rm -rf /var/lib/apt/lists/*
ENV DEBIAN_FRONTEND=dialog

# Ubuntu 24.04 marks the system python as externally managed
RUN pip3 install --break-system-packages pytest-xdist pytest-forked

# Set up auto-source of workspace for ros user
ARG WORKSPACE
RUN echo "if [ -f ${WORKSPACE}/install/setup.bash ]; then source ${WORKSPACE}/install/setup.bash; fi" >> /home/ros/.bashrc

RUN echo "export ROS_DOMAIN_ID=30" >> /home/ros/.bashrc
