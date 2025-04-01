#!/bin/bash

# Set timezone to KST
export TZ=Asia/Seoul

# Function to run the paper collection
run_collection() {
    echo "Starting paper collection at $(date '+%Y-%m-%d %H:%M:%S %Z')"
    PYTHONPATH=. python src/daily_top10.py
    echo "Paper collection completed at $(date '+%Y-%m-%d %H:%M:%S %Z')"
}

# Check if --now flag is provided
if [ "$1" = "--now" ]; then
    run_collection
    exit 0
fi

# Calculate next run time (3 AM KST)
next_run=$(date -d "3:00" +%s)
current_time=$(date +%s)

# If current time is past 3 AM, schedule for next day
if [ $current_time -gt $next_run ]; then
    next_run=$(date -d "tomorrow 3:00" +%s)
fi

# Calculate sleep time
sleep_time=$((next_run - current_time))

echo "Next run scheduled for $(date -d @$next_run '+%Y-%m-%d %H:%M:%S %Z')"
echo "Sleeping for $((sleep_time/3600)) hours and $(((sleep_time%3600)/60)) minutes"

# Sleep until next run time
sleep $sleep_time

# Run the collection
run_collection

# Schedule next run
while true; do
    # Sleep for 24 hours
    sleep 86400
    run_collection
done 