export async function fetchProgramSignatures(connection, programId, limit = 100) {
    return connection.getSignaturesForAddress(programId, { limit });
}
