$(document).ready(function() {
    $('#show-products').click(function() {
        $.ajax({
            url: 'https://127.0.0.1:7100/products',
            method: 'GET',
            success: function(data) {
                $('#product-list').empty(); // Clear previous products
                if (data.products.length === 0) {
                    $('#product-list').append('<p>No products available.</p>');
                } else {
                    data.products.forEach(function(product) {
                        $('#product-list').append(
                            `<div>
                                <h3>${product.name}</h3>
                                <p>${product.description}</p>
                                <p>Price: $${product.price}</p>
                                <img src="${product.image_path}" alt="${product.name}" width="200">
                            </div>`
                        );
                    });
                }
            },
            error: function() {
                alert('Error fetching products.');
            }
        });
    });
});
