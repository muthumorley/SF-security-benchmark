public inherited sharing class AccountManagerView {
    @AuraEnabled(cacheable=true)
    public static List<Account> getManagedAccounts(String industryFilter) {
        return [SELECT Id, Name, Industry, AnnualRevenue
                FROM Account
                WHERE Industry = :industryFilter
                WITH USER_MODE LIMIT 200];
    }
}
