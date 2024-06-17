function callPythonFunction() {
    const number1 = parseFloat(document.getElementById('number1').value);
    const number2 = parseFloat(document.getElementById('number2').value);

    fetch('http://127.0.0.1:5000/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ number1: number1, number2: number2 })
    })
    .then(response => response.json())
    .then(data => alert('Résultat: ' + data.result))
    .catch(error => console.error('Error:', error));
}

function generateAndShowImage() {
    fetch('http://127.0.0.1:5000/generate-image')
        .then(response => {
            if (response.ok) {
                document.getElementById('generatedImage').src = 'static/images/image.jpg';
                document.getElementById('generatedImage').style.display = 'block';
            } else {
                console.error('Error generating image');
            }
        })
        .catch(error => console.error('Error:', error));
}
