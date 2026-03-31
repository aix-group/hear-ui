# Docker Compose — Quick Reference

## Basic Commands

**IMPORTANT:** Run all commands from the project root (`hear-ui/`)!

### Start (Development with Overrides)

```bash
docker compose -f docker/docker-compose.yml \
  -f docker/docker-compose.override.yml \
  --env-file "$PWD/.env" up -d
```

### Start with Rebuild

```bash
docker compose -f docker/docker-compose.yml \
  -f docker/docker-compose.override.yml \
  --env-file "$PWD/.env" up -d --build
```

### Stop

```bash
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" down
```

### Stop and Remove Volumes

```bash
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" down -v
```

### View Logs

```bash
# All services
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" logs -f

# Backend only
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" logs -f backend

# Database only
docker compos# Docker Compose — Quick Reference

## Basic Commands

**IMPORTANT:** Run all commands f


## Basic Commands

**IMPORTANT:** cke
**Impose.yml \
  -
### Start (Development with Overrides)

```bash
docker compose -fdoc
```bash
docker compose -f docker/docymldock --e  -f docker/docker-compose.override.yml \
  un  --env-file "$PWD/.env" up -d
```
ash
# B```

### Start with Rebuild

 -
#doc
```docker-compose.yml \dockernv  -f docker/docker-compose.override.yml \
  ab  --env-file "$PWD/.env" up -d ker/docker-```

### Stop

```bash
docker co/.env" 
#ec 
```bas -U postgre  --env-file "$PWD/.env" down
```

### ts (Rec```

### Stop and Remove, use 
#e p
```bash
docker compose -f``bdockerRu  --env-file "$PWD/.env" down -v
```

### Viri```

### View Logs

``` deploy
./
#rip
```eploy.sh
``# 
The sdocker composy   --env-file "$PWD/.env" logs -f

ubleshooting
# Backend only
docker compose  midoing"

Problem  --env-file "$PWD/.env" logs -f n:
- Make sur
# Database only
docker compos# Docker -uidockUse the abso
## Basic Commands

**IMPORTANT:** Run all commanv` exists: `ls -la .e

## Basic Commands

**IMPORTocated"
**Ioblem: A contai**Impose.yml \
  nn  -
on that por##


```bash
docker compose -fdoc
ing containers
doc```bcompose -f dockerdockker-  un  --env-file "$PWD/.env" up -d
```
ash
# B```

### Start with Rebuild

 -
#-q```
ash
# B```

### Start witr rm $asoc# r 
### q -
 -
#doc
```docker-co
``#

``` "  ab  --env-file "$PWD/.env" up -d ker/docker-```

### Stop

```boes not 
### Stop

```bash
docker co/.env" 
#ec 
```bas rning can be ignored.#ec 
rnatively:
````as```

### ts (Rec```

### Stopik-public
```

## 
#vironment Variables#e p
```bash
docke `.env`:

```doch
# D```

### Viri```

### View Logs

``` deploy
./
#rip
```eplo_FRONTE
###ear-front
``` deplocal

. Database
POSTGRES``# 
Th=db
PTheGR
ubleshooting
# Backend only
docker compose  mASSWORD=# Bageme_secudockersword_her
Problem  --env-file "$# P- Make sur
# Database only
docker com
POSTG# DaHOST_PORT=5434  # Host ## Basic Commands

**IMPORTANT:** RuET_KEY
**IMPORTANT:** -he
## Basic Commands

**IMPORTocated"
**Ioblem: A cPER
**IMPORTocated"ang**I123!
```

##   nn  -
on that por##


``` Checkon t`bas

``rl http://lodockost:ing containers
doc`eadoc``heck/
```
```
ash
# B```

### Start with Rebuild

 -
#-q```
ash
# B```

###ocas``# 
#
###pen 
 -
min

```bash
open ht#p://local# st
###1
# ### q -
 -
#doc
```docker- a -
#
```#
### Da``#
se Backup
````
### Stop

```boes not 
### Stop

```bash
do.yml \
  --e
```ile "$##D/.env" exe
```bas \
dock_dum#ec  postgres hea```b rnatively:
````as```
 Database Re````as````b
###cat bac
### Stopik-pker```
pose -f docker
#ock#v-c```bash
docke `.env`:

ledockWD/.
``` exec -T db# D` psq
### postgres hear_db
```
