# Setup steps

## Local database for development and testing

Before you do anything you need to create the local database. First within your `.env` file add an environment variable called `SQLALCHEMY_DATABASE_URI`. An example SQLite database connection URI would be

`SQLALCHEMY_DATABASE_URI='sqlite:///test.db'`

Then on your command line use the following command

`flask create-db`

This creates the database with at the location specified by the connection URI

## Remote database for production

TODO

## Creating a migration or applying existing migrations

Migrations are how we keep track of any updates we do to the database schema. This way we can add/remove/edit tables without recreating the database (and thus removing all of the data we previously added)

### Initial migration

If no migrations have been created yet you need to first setup your local migration environment. After creating the initial database you must run the command

`flask db init`

This will create a 'migrations' folder in the project base directory. From here you need to commit your first migration. You can do that by the following commands

```
flask db migrate -m "Initial commit"
flask db upgrade
```

The first line just stages the first migration, it does not write it to any files yet. `flask db upgrade` takes the changes you commited and creates a migration file.