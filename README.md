# COVID effect notebook viewer

## Domains
 - https://covid.view.urbanobservatory.ac.uk [**ALPHA**]

## Deployment for Urban Observatory
 
### Running notebooks automatically

As an interim measure, using `crontab` under a local user to run `nbconvert`.

```
*/5 *  *   *   *     /bin/bash -c 'docker exec covid-notebook jupyter nbconvert --to html --execute --output-dir=/home/jovyan/movement-dashboard/output/ --ExecutePreprocessor.timeout=300 --no-input --template basic /home/jovyan/movement-dashboard/notebooks/update-pedestrian-flows.ipynb'
*/15 *  *   *   *    /bin/bash -c 'docker exec covid-notebook jupyter nbconvert --to html --execute --output-dir=/home/jovyan/movement-dashboard/output/ --ExecutePreprocessor.timeout=300 --no-input --template basic /home/jovyan/movement-dashboard/notebooks/update-car-park-occupancy.ipynb'

*/15 *  *   *   *    /bin/bash -c 'docker exec covid-notebook jupyter nbconvert --to html --execute --output-dir=/home/jovyan/movement-dashboard/output/ --ExecutePreprocessor.timeout=300 --no-input --template basic /home/jovyan/movement-dashboard/notebooks/plot-car-park-occupancy-6-months.ipynb'
*/15 *  *   *   *    /bin/bash -c 'docker exec covid-notebook jupyter nbconvert --to html --execute --output-dir=/home/jovyan/movement-dashboard/output/ --ExecutePreprocessor.timeout=300 --no-input --template basic /home/jovyan/movement-dashboard/notebooks/plot-car-park-occupancy-6-weeks.ipynb'
*/5 *  *   *   *     /bin/bash -c 'docker exec covid-notebook jupyter nbconvert --to html --execute --output-dir=/home/jovyan/movement-dashboard/output/ --ExecutePreprocessor.timeout=300 --no-input --template basic /home/jovyan/movement-dashboard/notebooks/plot-ncl-summary-of-pedestrian-flows.ipynb'
*/5 *  *   *   *     /bin/bash -c 'docker exec covid-notebook jupyter nbconvert --to html --execute --output-dir=/home/jovyan/movement-dashboard/output/ --ExecutePreprocessor.timeout=300 --no-input --template basic /home/jovyan/movement-dashboard/notebooks/plot-ncl-pedestrian-flows-28-days.ipynb'
*/5 *  *   *   *     /bin/bash -c 'docker exec covid-notebook jupyter nbconvert --to html --execute --output-dir=/home/jovyan/movement-dashboard/output/ --ExecutePreprocessor.timeout=300 --no-input --template basic /home/jovyan/movement-dashboard/notebooks/plot-ncl-comparison-to-typical-pedestrian-flows.ipynb'
```

Processing a notebook to HTML compatible with this viewer should look something like...
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
