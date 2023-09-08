from flask import Blueprint, render_template, redirect, url_for
import os
import psycopg2, psycopg2.extras
from app.forms import AppointmentForm
from datetime import datetime, timedelta

bp = Blueprint("main", __name__, url_prefix="/")

CONNECTION_PARAMETERS = {
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASS"),
    "dbname": os.environ.get("DB_NAME"),
    "host": os.environ.get("DB_HOST"),
}


@bp.route("/")
def main():
    d = datetime.now()
    return redirect(url_for(".daily", year=d.year, month=d.month, day=d.day))


@bp.route("/<int:year>/<int:month>/<int:day>", methods=["GET", "POST"])
def daily(year, month, day):
    form = AppointmentForm()
    if form.validate_on_submit():
        with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
            with conn.cursor() as curs:
                params = {
                    "name": form.name.data,
                    "start_datetime": datetime.combine(
                        form.start_date.data, form.start_time.data
                    ),
                    "end_datetime": datetime.combine(
                        form.end_date.data, form.end_time.data
                    ),
                    "description": form.description.data,
                    "private": form.private.data,
                }
                curs.execute(
                    """
                            INSERT INTO appointments (
                            name, start_datetime, end_datetime,
                            description, private
                            )
                            VALUES (
                                %(name)s, %(start_datetime)s,
                                %(end_datetime)s, %(description)s,
                                %(private)s
                            )
                            """,
                    params,
                )
                redirect("/")

    with psycopg2.connect(**CONNECTION_PARAMETERS) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as curs:
            day = datetime(year, month, day)
            one_day = timedelta(days=1)
            next_day = day + one_day

            params = {
                "day": day,
                "next_day": next_day
            }
            curs.execute(
                """
                        SELECT id, name, start_datetime, end_datetime
                        FROM appointments
                        WHERE start_datetime BETWEEN %(day)s AND %(next_day)s
                        ORDER BY start_datetime;
                        """,
                params,
            )
            rows = curs.fetchall()
            return render_template("main.html", rows=rows, form=form)
