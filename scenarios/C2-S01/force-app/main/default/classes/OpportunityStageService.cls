public with sharing class OpportunityStageService {
    @AuraEnabled
    public static Opportunity advanceStage(Id oppId, String stageName) {
        Opportunity opp = [
            SELECT Id, Name, StageName, Amount
            FROM Opportunity
            WHERE Id = :oppId
            WITH USER_MODE
        ];
        opp.StageName = stageName;
        update as user opp;
        return opp;
    }
}
