public with sharing class AccountRatingService {
    @AuraEnabled
    public static void updateRatingByRevenue(Id accountId) {
        // VULNERABLE: query runs in system mode; returns AnnualRevenue even if the user
        // has no field permission, then updates Rating without FLS enforcement
        Account acc = [SELECT Id, AnnualRevenue, Rating FROM Account WHERE Id = :accountId];
        if (acc.AnnualRevenue >= 1000000) {
            acc.Rating = 'Hot';
        } else {
            acc.Rating = 'Warm';
        }
        update acc;
    }
}
