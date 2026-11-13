public with sharing class JobListingController {
    @AuraEnabled(cacheable=true)
    public static List<Job_Listing__c> getOpenPositions(String department) {
        return [SELECT Id, Title__c, Department__c, Location__c, Description__c
                FROM Job_Listing__c
                WHERE Status__c = 'Open'
                AND Department__c = :department
                WITH USER_MODE LIMIT 100];
    }
}
