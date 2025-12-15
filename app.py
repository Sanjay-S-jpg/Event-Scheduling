from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
#from models import Event, Resource, EventResourceAllocation
from flask import flash, redirect, url_for


app = Flask(__name__)
app.secret_key = "secret"

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:poilkj09@localhost/event_scheduler' # Update with your actual database password after the root:______@localhost
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)



class Event(db.Model):
    event_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    description = db.Column(db.Text)


class Resource(db.Model):
    resource_id = db.Column(db.Integer, primary_key=True)
    resource_name = db.Column(db.String(255))
    resource_type = db.Column(db.String(100))


class EventResourceAllocation(db.Model):
    allocation_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.event_id'))
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.resource_id'))


with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return redirect(url_for('events'))


@app.route('/events', methods=['GET', 'POST'])
def events():
    if request.method == 'POST':
        title = request.form['title']
        start = datetime.strptime(request.form['start'], '%Y-%m-%dT%H:%M')
        end = datetime.strptime(request.form['end'], '%Y-%m-%dT%H:%M')

        if start >= end:
            flash("Invalid time range")
            return redirect(url_for('events'))

        event = Event(title=title, start_time=start, end_time=end,
                      description=request.form['description'])
        db.session.add(event)
        db.session.commit()

    events = Event.query.all()
    return render_template('events.html', events=events)

@app.route('/resources', methods=['GET', 'POST'])
def resources():
    if request.method == 'POST':
        resource = Resource(
            resource_name=request.form['name'],
            resource_type=request.form['type']
        )
        db.session.add(resource)
        db.session.commit()

        flash("Resource added successfully!")
        print("FLASH STORED")
        return redirect(url_for('resources'))

    resources = Resource.query.all()
    return render_template('resources.html', resources=resources)


@app.route('/allocate', methods=['GET', 'POST'])
def allocate():
    events = Event.query.all()
    resources = Resource.query.all()

    if request.method == 'POST':
        event_id = int(request.form['event'])
        resource_id = int(request.form['resource'])

        event = Event.query.get(event_id)

        allocations = EventResourceAllocation.query.filter_by(resource_id=resource_id).all()

        for alloc in allocations:
            other_event = Event.query.get(alloc.event_id)
            if event.start_time < other_event.end_time and event.end_time > other_event.start_time:
                flash("Resource conflict detected!")
                return redirect(url_for('allocate'))

        allocation = EventResourceAllocation(event_id=event_id, resource_id=resource_id)
        db.session.add(allocation)
        db.session.commit()

        flash("Resource allocated successfully!")
        return redirect(url_for('allocate'))


    return render_template('allocate.html', events=events, resources=resources)

@app.route('/report', methods=['GET', 'POST'])
def report():
    data = []

    if request.method == 'POST':
        start = datetime.strptime(request.form['start'], '%Y-%m-%d')
        end = datetime.strptime(request.form['end'], '%Y-%m-%d')

        for r in Resource.query.all():
            total_hours = 0
            upcoming = 0

            allocations = EventResourceAllocation.query.filter_by(resource_id=r.resource_id).all()
            for a in allocations:
                e = Event.query.get(a.event_id)
                if e.start_time >= start and e.end_time <= end:
                    total_hours += round((e.end_time - e.start_time).seconds / 3600, 2)

                if e.start_time > datetime.now():
                    upcoming += 1

            data.append((r.resource_name, total_hours, upcoming))

    return render_template('report.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
