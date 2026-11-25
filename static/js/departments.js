// One shared list of departments, used by the signup page and the "Add New Project" form.
// To add or rename a department, edit this list only.
window.DEPARTMENTS = [
  "Computer Science and Engineering",
  "Computer Science and Engineering (AI)",
  "Computer Science and Engineering (AI & ML)",
  "Computer Science and Engineering (Data Science)",
  "Computer Science and Engineering (Cyber Security)",
  "Computer Science and Engineering (IoT)",
  "Artificial Intelligence and Data Science",
  "Artificial Intelligence and Machine Learning",
  "Information Science and Engineering",
  "Information Technology",
  "Electronics and Communication Engineering",
  "Electronics and Computer Engineering",
  "Electrical and Electronics Engineering",
  "Electrical Engineering",
  "Mechanical Engineering",
  "Mechatronics Engineering",
  "Robotics and Automation",
  "Automobile Engineering",
  "Aerospace Engineering",
  "Civil Engineering",
  "Chemical Engineering",
  "Biotechnology",
  "Industrial Engineering and Management",
  "Computer Applications (BCA / MCA)",
  "Business Administration (MBA)",
  "Mathematics",
  "Physics",
  "Chemistry",
  "Other"
];

// Fill the department box on the student's "Add New Project" form, if this page has one.
document.addEventListener('DOMContentLoaded', function () {
  var sel = document.getElementById('projectDepartment');
  if (!sel) return;
  sel.innerHTML = '<option value="">Select Department</option>' +
    window.DEPARTMENTS.map(function (d) { return '<option value="' + d + '">' + d + '</option>'; }).join('');
});
