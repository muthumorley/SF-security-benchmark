public inherited sharing class MyAccountsController {
    @AuraEnabled(cacheable=true)
    public static List<Account> getMyAccounts() {
        return [
            SELECT Id, Name, Type
            FROM Account
            WHERE OwnerId = :UserInfo.getUserId()
            WITH SECURITY_ENFORCED
            LIMIT 100
        ];
    }
}
