# COVID effect notebook viewer

## Domains
 - https://covid.view.urbanobservatory.ac.uk [**ALPHA**]

## Deployment for Urban Observatory
 
### Running notebooks automatically

As an interim measure, using `crontab` under a local user to run `nbconvert`.

The command should look something like this:
```
docker exec covid-notebook \
  jupyter nbconvert \
    --to html \
	--execute \
	--output-dir=/home/jovyan/movement-dashboard/output/ \
	--ExecutePreprocessor.timeout=3000 \
	--no-input \
	--template basic \
	/home/jovyan/movement-dashboard/plot-pedestrian-flows.ipynb
```

### Firewall changes

The notebooks do not run under the 'web' network on our server, and require a firewall rule to allow the notebook's own local network to connect to Traefik.

```
ufw allow from 192.168.0.0/16 to any port 443
```
