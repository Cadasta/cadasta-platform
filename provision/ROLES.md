| Name                  | Dev? | Prod? | Description |
|-----------------------|------|-------|-------------|
| system/aws            |      |   X   | Create `cadasta` Linux user |
| system/common         |  X   |   X   | Set up `~/.pgpass` |
| db/common             |  X   |   X   | Configure Postgres APT |
| db/development        |  X   |       | Install Postgres server and other packages; set up local authentication; create Cadasta database, database user; install PostGIS |
| db/production         |      |   X   | Install Postgres client and other packages; create Cadasta database, database user; install PostGIS |
| cadasta/install       |      |   X   | Set up `/opt/cadasta`; clone `cadasta-platform` repo; set up environment variables |
| cadasta/application   |  X   |   X   | Create virtual environment; install requirements; Django migrate; build front-end |
| cadasta/development   |  X   |       | Install Python development requirements |
| cadasta/production    |      |   X   | Install Python production requirements; write templates for Inline Manual, Google Analytics |
| webserver/production  |      |   X   | Install nginx, uWSGI; set up uWSGI; set up production site configuration |
