// Manager dashboard: runs in system context to aggregate pipeline data across all reps.
// VULNERABLE: without sharing means partner community users calling this endpoint
// will see opportunities from all accounts, not just their own.
public without sharing class FinancialDashboardController {
    @AuraEnabled(cacheable=true)
    public static List<Opportunity> getPipelineSummary() {
        return [SELECT Id, Name, Amount, StageName, CloseDate FROM Opportunity
                WITH USER_MODE LIMIT 500];
    }
}
