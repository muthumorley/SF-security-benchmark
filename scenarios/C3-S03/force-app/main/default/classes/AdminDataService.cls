/**
 * Internal batch helper — NOT an AuraEnabled entry point.
 * Called only from AccountSyncBatch.execute() which runs as a scheduled admin job.
 * without sharing is intentional: the batch needs to read all records for a full
 * data sync regardless of the executing user's sharing rules.
 */
public without sharing class AdminDataService {
    public static List<Account> getAllAccountsForSync() {
        return [SELECT Id, Name, BillingCountry, AnnualRevenue, OwnerId
                FROM Account
                WHERE LastModifiedDate = LAST_N_DAYS:1
                LIMIT 10000];
    }
}
