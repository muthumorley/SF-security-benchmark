public with sharing class ContactLookupController {
    @AuraEnabled(cacheable=true)
    public static List<Contact> findByLastName(String lastName, String sortField) {
        Set<String> allowedSort = new Set<String>{ 'LastName', 'CreatedDate' };
        String orderBy = allowedSort.contains(sortField) ? sortField : 'LastName';
        String query = 'SELECT Id, FirstName, LastName FROM Contact '
            + 'WHERE LastName = :lastName ORDER BY ' + orderBy + ' LIMIT 50';
        return Database.queryWithBinds(
            query,
            new Map<String, Object>{ 'lastName' => lastName },
            AccessLevel.USER_MODE
        );
    }
}
