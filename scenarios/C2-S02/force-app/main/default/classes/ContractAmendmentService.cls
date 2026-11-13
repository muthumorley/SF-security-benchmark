public with sharing class ContractAmendmentService {
    @AuraEnabled
    public static List<Contract> getContractsForAmendment(Id accountId) {
        List<Contract> records = [
            SELECT Id, ContractNumber, Status, StartDate, Legal_Notes__c
            FROM Contract
            WHERE AccountId = :accountId
        ];
        // Strip any fields the running user cannot read (including Legal_Notes__c if denied)
        SObject[] stripped = Security.stripInaccessible(AccessType.READABLE, records).getRecords();
        return (List<Contract>) stripped;
    }

    @AuraEnabled
    public static void amendContract(Contract amendment) {
        update as user amendment;
    }
}
