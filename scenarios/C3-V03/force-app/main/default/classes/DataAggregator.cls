// VULNERABLE: DataAggregator is 'without sharing'. The @AuraEnabled entry point
// queries directly on this class. The inner helper's 'with sharing' keyword has
// no effect on queries executed in DataAggregator's own methods.
public without sharing class DataAggregator {

    public with sharing class SharedHelper {
        public static List<Lead> getMyLeads() {
            return [SELECT Id, Name, Status FROM Lead WITH USER_MODE LIMIT 100];
        }
    }

    @AuraEnabled(cacheable=true)
    public static List<Lead> getLeadSummary() {
        // This query runs in DataAggregator's context — without sharing —
        // even though SharedHelper exists. SharedHelper.getMyLeads() is never called.
        return [SELECT Id, Name, Status, Email FROM Lead WITH USER_MODE LIMIT 200];
    }
}
