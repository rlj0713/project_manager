fetch('/api/test')
    .then((response) => response.json())
    .then((data) => {
        document.getElementById('api-response').textContent = data.message;
    })
    .catch(() => {
        document.getElementById('api-response').textContent = 'API request failed';
    });