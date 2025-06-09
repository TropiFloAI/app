#!/usr/bin/env bash
rsync -avz --delete --partial \
  -e "ssh -o StrictHostKeyChecking=accept-new" \
  ./  \
  ozkilim@co-datascientist.io:/home/ozkilim/POC/app/

ssh ozkilim@co-datascientist.io 'sudo systemctl restart codatascientist'
