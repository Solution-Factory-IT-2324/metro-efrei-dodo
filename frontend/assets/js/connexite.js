document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('connexite-form');
    const resultContainer = document.getElementById('result-container');

    form.addEventListener('submit', event => {
        event.preventDefault();
        const method = document.getElementById('method').value;
        checkConnectivity(method);
    });

    const checkConnectivity = (method) => {
        fetch(`http://127.0.0.1:8080/api/graph/is-connected/${method}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 200) {
                    const result = data.data.result ? 'Le réseau est connecté.' : 'Le réseau n\'est pas connecté.';
                    resultContainer.innerHTML = `<p>Méthode: ${data.data.method.toUpperCase()}</p><p>${result}</p>`;
                } else {
                    resultContainer.innerHTML = '<p>Erreur lors de la vérification de la connexité.</p>';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                resultContainer.innerHTML = '<p>Erreur lors de la vérification de la connexité.</p>';
            });
    };
});
