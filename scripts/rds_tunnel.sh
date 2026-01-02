#!/bin/bash
# chmod +x rds_tunnel.sh
# rds_tunnel.sh

KEY_PATH= # E.g., path to aws key
EC2_HOST= # E.g., "ec2-user@<EC2 instance IP address>"
RDS_HOST= # E.g., "forecasting-db.xyz.us-east-2.rds.amazonaws.com"
LOCAL_PORT=15432
REMOTE_PORT=5432

start_adminer() {
  echo "Ensuring Adminer is running on EC2..."

  ssh -i "$KEY_PATH" $EC2_HOST << 'EOF'
    # Check if Adminer is running
    RUNNING=$(sudo docker ps --filter "name=adminer" --format "{{.Names}}")

    if [ "$RUNNING" != "adminer" ]; then
      echo "Adminer is not running, starting it..."

      # Remove old container if exists
      sudo docker rm -f adminer >/dev/null 2>&1

      # Start Adminer bound to localhost only (more secure)
      sudo docker run -d --name adminer -p 127.0.0.1:8080:8080 adminer

      echo "Adminer started."
    else
      echo "Adminer already running."
    fi
EOF
}

case "$1" in
  tunnel)
    echo "Starting SSH tunnel to RDS..."
    ssh -i "$KEY_PATH" -L ${LOCAL_PORT}:${RDS_HOST}:${REMOTE_PORT} $EC2_HOST -N &
    echo "Tunnel started on localhost:${LOCAL_PORT}"
    echo "Use: psql -h localhost -p ${LOCAL_PORT} -U postgres -d appdb"
    ;;

  adminer)
    start_adminer
    echo "Forwarding Adminer (localhost:8080)..."
    ssh -i "$KEY_PATH" -L 8080:localhost:8080 $EC2_HOST
    ;;

  ssh)
    echo "Connecting to EC2..."
    ssh -i "$KEY_PATH" $EC2_HOST
    ;;

  *)
    echo "Usage: ./rds_tunnel.sh [tunnel|adminer|ssh]"
    ;;
esac
