# programmable-teaching
scripting teaching

### Assignments on Canvas

Script to find ungraded assignments: <https://github.com/KTH/devops-course/blob/2024/tools/missing_grade.py> (2024 edition in branch 2024)

### Grading

```
#!/bin/bash
CANVAS_TOKEN=8779~foobar
CANVAS_COURSE_ID=48942 # 2024 edition
python final_grade_exporter.py --token $CANVAS_TOKEN --course $CANVAS_COURSE_ID
```

