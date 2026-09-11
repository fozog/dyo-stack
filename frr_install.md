
```
sudo apt install frr frr-pythontools
```

enable ripd in /etc/frr/daemons and restart the service

```
sed -i -E 's/\brpid=[^[:space:]]+/rpid=yes/' /etc/frr/daemons
sudo systemctl restart frr
```

