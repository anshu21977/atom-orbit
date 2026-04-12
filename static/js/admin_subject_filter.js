document.addEventListener('DOMContentLoaded', function () {
    const classField = document.getElementById('id_classroom');
    const subjectField = document.getElementById('id_subject');

    classField.addEventListener('change', function () {
        const classId = this.value;

        fetch(`/load-subjects/?class_id=${classId}`)
            .then(response => response.json())
            .then(data => {
                subjectField.innerHTML = '<option value="">---------</option>';

                data.forEach(subject => {
                    const option = document.createElement('option');
                    option.value = subject.id;
                    option.textContent = subject.name;
                    subjectField.appendChild(option);
                });
            });
    });
});