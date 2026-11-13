public with sharing class AccountSearchController {
    @AuraEnabled(cacheable=true)
    public static List<Account> searchAccounts(String searchKey) {
        String query = 'SELECT Id, Name, Industry FROM Account '
            + 'WHERE Name LIKE \'%' + searchKey + '%\' LIMIT 50';
        return Database.query(query, AccessLevel.USER_MODE);
    }
}
