#!/usr/bin/python
# -*- coding: utf-8 -*-
# Compute the final grade of a course
# based on data from the Canvas API
# the grading formula is in compute_grade(completed_assignments)
# Last used for Devops, Oct 2024
# Author Monperrus
# URL: https://github.com/monperrus/programmable-teaching


import csv
import json
import argparse, requests

CANVAS_TOKEN = ''
EXPORT_PATH = ''
FIELDS = ''
CANVAS_URL = "https://canvas.kth.se"
CANVAS_COURSE_ID = 0

GH_KTH_MAPPING = [x+"@kth.se" for x in json.load(open("gh_to_kth.json")).values()]


def get_email(user):
    if "email" in user: return user["email"]
    if "login_id" in user: return user["login_id"]
    return "<unknown_email>"

# Get list of students {canvas_id, name, kth_id}
def get_students():
    url = "{0}/api/v1/courses/{1}/users?per_page=100&enrollment_type[]=student".format(CANVAS_URL, CANVAS_COURSE_ID)
    result = []
    while url:
        r = requests.get(url, headers={'Authorization': 'Bearer ' + CANVAS_TOKEN})
        data = json.loads(r.content)
        url = None
        if 'next' in r.links:
            url = r.links["next"]["url"]
        result = result + [{"canvas_id": user["id"], "name": user["name"], "kth_id": get_email(user)} for user in
            data]

    return result


# Get graded submission with complete grade for a canvas user, list of assignments name
def get_completed_submissions(canvas_id):
    url = "{0}/api/v1/courses/{1}/students/submissions?workflow_state=graded&student_ids[]={2}&include[]=assignment".format(
        CANVAS_URL,
        CANVAS_COURSE_ID,
        canvas_id)
    r = requests.get(url, headers={'Authorization': 'Bearer ' + CANVAS_TOKEN})
    return [submission["assignment"]["name"] for submission in json.loads(r.content) if
            submission["grade"] == "complete"]


# Compute the grade according to the number of completed assignments
# Ignore feedback for grade E
def compute_grade(completed_assignments, kth_id):
    for x in completed_assignments:
        if x not in ['Presentations', 'Scientific Papers', 'Demos', 'Executable Tutorials', 'Feedback', 'Open-source contributions']: completed_assignments.remove(x)
        
    # print(completed_assignments)
    if "First Lecture Attendance" in completed_assignments: completed_assignments.remove("First Lecture Attendance") 
    # 
    nb_assignments = len(completed_assignments)

    if "Presentations" not in completed_assignments and "Demos" not in completed_assignments:
        return "F"

    if nb_assignments >= 5:
        # now check for attendance
        if kth_id in GH_KTH_MAPPING: return "A"
        
        return "B"
    elif nb_assignments == 4:
        return "C"
    elif nb_assignments == 3 and "Feedback" not in completed_assignments:
        return "E"
    else:
        return "F"


# Parse arguments of the script
def parse_args():
    global CANVAS_COURSE_ID
    global CANVAS_TOKEN
    global EXPORT_PATH
    global FIELDS
    parser = argparse.ArgumentParser()

    parser.add_argument('--course', dest='course', type=str, help='Canvas course ID', required=True)
    parser.add_argument('--token', dest='token', type=str, help='Canvas access token', required=True)
    parser.add_argument('--fields', dest='fields', type=str, nargs='+', help='Fiedls to export',
                        default=["name", "kth_id", "grade"])
    parser.add_argument('--export', dest='export_path', type=str, help='Path to write csv file', required=False,
                        default='')

    args = parser.parse_args()
    CANVAS_COURSE_ID = args.course
    CANVAS_TOKEN = args.token
    EXPORT_PATH = args.export_path
    FIELDS = args.fields


def main():
    parse_args()

    students = get_students()

    
    # Get completed assignments for each students and compute the grade
    for i in range(0, len(students)):
        # print(students[i]["kth_id"])
        completed = get_completed_submissions(students[i]["canvas_id"])
        students[i]["completed"] = completed
        students[i]["grade"] = compute_grade(completed, students[i]["kth_id"])
        #print("{0},{1},{2}".format(students[i]["name"], students[i]["kth_id"], students[i]["grade"]))
        # canvaslm version
        #  canvaslms grade -c 48942 -a "test assignment" -u sorger -g B
        if students[i]["grade"] != 'F':
            print("{0},{1},{2}".format(students[i]["name"], students[i]["kth_id"], students[i]["grade"]))
            print("canvaslms grade -c 48942 -a 'final' -u {1} -g {2}".format(students[i]["name"], students[i]["kth_id"], students[i]["grade"]))

    if EXPORT_PATH != '':
        # Write the result to csv file
        with open(EXPORT_PATH, mode='w') as grade_file:
            grade_writer = csv.DictWriter(grade_file, delimiter=',', fieldnames=FIELDS,
                                          extrasaction='ignore')
            grade_writer.writeheader()
            grade_writer.writerows(students)


main()
