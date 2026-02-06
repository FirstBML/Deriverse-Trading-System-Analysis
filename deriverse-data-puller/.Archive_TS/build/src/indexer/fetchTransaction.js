export async function fetchTransaction(connection, signature) {
    return connection.getTransaction(signature, {
        commitment: 'confirmed',
        maxSupportedTransactionVersion: 0,
    });
}
