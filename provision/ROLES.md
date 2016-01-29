| Name                  | Dev? | Prod? | Description |
|-----------------------|------|-------|-------------|
| system/aws            |      |   X   | Create `cadasta` Linux user |
| system/common         |  X   |   X   | Set up `~/.pgppass` |
| db/common             |  X   |   X   | Configure Postgres APT |
| db/development        |  X   |       | Install Postgres server and other packages; set up local authentication; create Cadasta database, database user; install PostGIS |
| db/production         |      |   X   | Install Postgres client and other packages; create Cadasta database, database user; install PostGIS |
| cadasta/install       |      |   X   | Set up `/opt/cadasta`; clone `cadasta-platform` repo; set up environment variables |
| cadasta/application   |  X   |   X   | Create virtual environment; install requirements; Django migrate; build front-end |
| cadasta/development   |  X   |       | Install Python development requirements |
| webserver/common      |  X   |   X   | Install nginx |
| webserver/development |  X   |       | Set up development site configuration |
| webserver/production  |      |   X   | Install uWSGI; set up uWSGI emperor process; set up production site configuration; set up uWSGI |
