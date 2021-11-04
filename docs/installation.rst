.. highlight:: shell

============
Installation
============

Prerequisites
-------------

- `python3.7 <https://realpython.com/installing-python/>`_

- `Git <https://github.com/git-guides/install-git>`_

- `Postgresql <https://www.postgresql.org/download/>`_

- `Heroku CLI <https://medium.com/analytics-vidhya/how-to-install-heroku-cli-in-windows-pc-e3cf9750b4ae>`_

- `Pip <https://phoenixnap.com/kb/install-pip-windows>`_

Note that you may use another Python installer (instead of Pip), Host (instead of Heroku) or Database (instead of Postgresql) but that will require you figuring out the required setup and configuation changes yourself.

Installing
----------

We recommend using `virtual environments <https://docs.python.org/3/tutorial/venv.html>`_ to manage python packages for our repo. To clone the repo and install dependencies, run the following on the command line

.. code-block:: console
    
    $ # Clone the bot locally
    $ git clone https://github.com/kevslinger/bot-be-named.git
    $ cd bot-be-named
    $ virtualenv venv -p=3.7
    $ # This installs all the python dependencies the bot needs
    $ pip install -r requirements.txt

The bot uses `Heroku Postgres <https://www.heroku.com/postgres>`_ for storing data.

To run the bot locally, you will need a ``.env`` file which is used by `python-dotenv <https://github.com/theskumar/python-dotenv>`_ to load ``ENV`` variables. Copy ``.env.template`` into ``.env`` with  

.. code-block:: console
    
    $ cp .env.template .env

and fill in the blanks in order to get the bot running. You also need to set up the Postgresql database for the bot. You can follow the `postgres download <https://www.postgresql.org/download/>`_ link.

Once you do all that, run

.. code-block:: console

    $ source venv/bin/activate
    $ python bot.py


and the bot will run on the supplied discord token's account.

.. _Github repo: https://github.com/kevslinger/bot-be-named











