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