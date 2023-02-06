# hiddifypanel Flask Application

 hiddifypanel to create multi proxy using xray mtproxy and others

# under development do not use it yet
## Installation

From source:

```bash
git clone https://github.com/hiddify/HiddifyPanel hiddifypanel
cd hiddifypanel
make install
```

From pypi:

```bash
pip install hiddifypanel
```

## Executing

This application has a CLI interface that extends the Flask CLI.

Just run:

```bash
$ hiddifypanel
```

or

```bash
$ python -m hiddifypanel
```

To see the help message and usage instructions.

## First run

```bash
hiddifypanel init-db   # run once
echo localhost:9000/$(hiddifypanel admin-path)
hiddifypanel run
```


> **Note**: You can also use `flask run` to run the application.
